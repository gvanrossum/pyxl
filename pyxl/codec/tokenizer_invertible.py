#!/usr/bin/env python

from . import pytokenize as tokenize
import re
from io import StringIO
from pyxl.codec.parser import PyxlParser
from .pytokenize import Untokenizer
import ast

class PyxlUnfinished(Exception): pass

class PyxlParseError(Exception): pass

def get_end_pos(start_pos, tvalue):
    row, col = start_pos
    for c in tvalue:
        if c == '\n':
            col = 0
            row += 1
        else:
            col += 1
    return (row, col)

class RewindableTokenStream(object):
    """
    A token stream, with the ability to rewind and restart tokenization while maintaining correct
    token position information.

    Invariants:
        - zero_row and zero_col are the correct values to adjust the line and possibly column of the
        tokens being produced by _tokens.
        - Tokens in unshift_buffer have locations with absolute position (relative to the beginning
          of the file, not relative to where we last restarted tokenization).
    """

    def __init__(self, readline):
        self.orig_readline = readline
        self.unshift_buffer = []
        self.rewound_buffer = None
        self._tokens = tokenize.generate_tokens(self._readline)
        self.zero_row, self.zero_col = (0, 0)
        self.stop_readline = False

    def _dumpstate(self):
        print("tokenizer state:")
        print("  zero:", (self.zero_row, self.zero_col))
        print("  rewound_buffer:", self.rewound_buffer)
        print("  unshift_buffer:", self.unshift_buffer)

    def _readline(self):
        if self.stop_readline:
            return ""
        if self.rewound_buffer:
            line = self.rewound_buffer.readline()
            if line:
                return line
            else:
                self.rewound_buffer = None  # fallthrough to orig_readline
        return self.orig_readline()

    def _flush(self):
        self.stop_readline = True
        tokens = list(tok for tok in self)
        self.stop_readline = False
        return tokens

    def _adjust_position(self, pos):
        row, col = pos
        if row == 1:  # rows are 1-indexed
            col += self.zero_col
        row += self.zero_row
        return (row, col)

    def rewind_and_retokenize(self, rewind_token):
        """Rewind the given token (which is expected to be the last token read from this stream, or
        the end of such token); then restart tokenization."""
        ttype, tvalue, (row, col), tend, tline = rewind_token
        tokens = [rewind_token] + self._flush()
        self.zero_row, self.zero_col = (row - 1, col)  # rows are 1-indexed, cols are 0-indexed
        self.rewound_buffer = StringIO(Untokenizer().untokenize(tokens))
        self.unshift_buffer = []
        self._tokens = tokenize.generate_tokens(self._readline)

    def __next__(self):
        if self.unshift_buffer:
            token = self.unshift_buffer.pop(0)
        else:
            ttype, tvalue, tstart, tend, tline = next(self._tokens)
            tstart = self._adjust_position(tstart)
            tend = self._adjust_position(tend)
            token = (ttype, tvalue, tstart, tend, tline)
        return token

    def __iter__(self):
        return self

    def unshift(self, token):
        """Rewind the given token, without retokenizing. It will be the next token read from the
        stream."""
        self.unshift_buffer[:0] = [token]

def pyxl_untokenize(tokens):
    parts = []
    prev_row = 1
    prev_col = 0

    for token in tokens:
        ttype, tvalue, tstart, tend, tline = token
        row, col = tstart

        assert row == prev_row, 'Unexpected jump in rows on line:%d: %s' % (row, tline)

        # Add whitespace
        col_offset = col - prev_col
        assert col_offset >= 0
        if col_offset > 0:
            parts.append(" " * col_offset)

        parts.append(tvalue)
        prev_row, prev_col = tend

        if ttype in (tokenize.NL, tokenize.NEWLINE):
            prev_row += 1
            prev_col = 0

    return ''.join(parts)

def pyxl_tokenize(readline):
    return transform_tokens(RewindableTokenStream(readline))

def pyxl_reverse_tokenize(readline):
    return cleanup_tokens(reverse_tokens(RewindableTokenStream(readline)))

def transform_tokens(tokens):
    last_nw_token = None
    prev_token = None

    curly_depth = 0

    while 1:
        try:
            token = next(tokens)
        except (StopIteration, tokenize.TokenError):
            break

        ttype, tvalue, tstart, tend, tline = token

        if ttype == tokenize.OP and tvalue == '{':
            curly_depth += 1
        if ttype == tokenize.OP and tvalue == '}':
            curly_depth -= 1
            if curly_depth < 0:
                tokens.unshift(token)
                return

        if (ttype == tokenize.OP and tvalue == '<' and
            (last_nw_token == None or # if we have *just* entered python mode e.g
             (last_nw_token[0] == tokenize.OP and last_nw_token[1] == '=') or
             (last_nw_token[0] == tokenize.OP and last_nw_token[1] == '(') or
             (last_nw_token[0] == tokenize.OP and last_nw_token[1] == '[') or
             (last_nw_token[0] == tokenize.OP and last_nw_token[1] == '{') or
             (last_nw_token[0] == tokenize.OP and last_nw_token[1] == ',') or
             (last_nw_token[0] == tokenize.OP and last_nw_token[1] == ':') or
             (last_nw_token[0] == tokenize.NAME and last_nw_token[1] == 'print') or
             (last_nw_token[0] == tokenize.NAME and last_nw_token[1] == 'else') or
             (last_nw_token[0] == tokenize.NAME and last_nw_token[1] == 'yield') or
             (last_nw_token[0] == tokenize.NAME and last_nw_token[1] == 'return'))):
            token = get_pyxl_token(token, tokens)
#            print("PYXL", token)

        if ttype not in (tokenize.INDENT,
                         tokenize.DEDENT,
                         tokenize.NL,
                         tokenize.NEWLINE,
                         tokenize.COMMENT):
            last_nw_token = token

        # strip trailing newline from non newline tokens
        if tvalue and tvalue[-1] == '\n' and ttype not in (tokenize.NL, tokenize.NEWLINE):
            ltoken = list(token)
            tvalue = ltoken[1] = tvalue[:-1]
            token = tuple(ltoken)

        # tokenize has this bug where you can get line jumps without a newline token
        # we check and fix for that here by seeing if there was a line jump
        if prev_token:
            prev_ttype, prev_tvalue, prev_tstart, prev_tend, prev_tline = prev_token

            prev_row, prev_col = prev_tend
            cur_row, cur_col = tstart

            # check for a line jump without a newline token
            if (prev_row < cur_row and prev_ttype not in (tokenize.NEWLINE, tokenize.NL)):

                # tokenize also forgets \ continuations :(
                prev_line = prev_tline.strip()
                if prev_ttype != tokenize.COMMENT and prev_line and prev_line[-1] == '\\':
                    start_pos = (prev_row, prev_col)
                    end_pos = (prev_row, prev_col+1)
                    yield (tokenize.STRING, ' \\', start_pos, end_pos, prev_tline)
                    prev_col += 1

                start_pos = (prev_row, prev_col)
                end_pos = (prev_row, prev_col+1)
                yield (tokenize.NL, '\n', start_pos, end_pos, prev_tline)

        prev_token = token
        yield token

def get_pyxl_token(start_token, tokens):
    ttype, tvalue, tstart, tend, tline = start_token
    pyxl_parser = PyxlParser(tstart[0], tstart[1])
    pyxl_parser.feed(start_token)

    seen = [start_token]
    python_stuff = []
    for token in tokens:
        ttype, tvalue, tstart, tend, tline = token


        if tvalue and tvalue[0] == '{':
            if pyxl_parser.python_mode_allowed():
                initial_tstart = tstart

                mid, right = tvalue[0], tvalue[1:]
                division = get_end_pos(tstart, mid)
                pyxl_parser.feed_position_only((ttype, mid, tstart, division, tline))
                tokens.rewind_and_retokenize((ttype, right, division, tend, tline))
                python_tokens = list(transform_tokens(tokens))

                close_curly = next(tokens)
                # seen.append(close_curly)
                ttype, tvalue, tstart, tend, tline = close_curly
                close_curly_sub = (ttype, '', tend, tend, tline)

                seen.append((ttype, '{{{}}}', initial_tstart, tend, ''))

                pyxl_parser.feed_python(python_tokens + [close_curly_sub])
                python_stuff.append(python_tokens + [close_curly_sub])
                continue
            # else fallthrough to pyxl_parser.feed(token)
        elif tvalue and ttype == tokenize.COMMENT:
            if not pyxl_parser.python_comment_allowed():
                tvalue, rest = tvalue[0], tvalue[1:]
                division = get_end_pos(tstart, tvalue)
                tokens.unshift((tokenize.ERRORTOKEN, rest, division, tend, tline))
                token = ttype, tvalue, tstart, division, tline
                # fallthrough to pyxl_parser.feed(token)
            else:
                seen.append(token)
                pyxl_parser.feed_comment(token)
                continue
        elif tvalue and tvalue[0] == '#':
            # let the python tokenizer grab the whole comment token
            tokens.rewind_and_retokenize(token)
            continue
        else:
            sp = re.split('([#{])', tvalue, maxsplit=1)
            if len(sp) > 1:
                tvalue, mid, right = sp
                division = get_end_pos(tstart, tvalue)
                tokens.unshift((ttype, mid+right, division, tend, tline))
                token = ttype, tvalue, tstart, division, tline
                # fallthrough to pyxl_parser.feed(token)

        seen.append(token)
        pyxl_parser.feed(token)

        if pyxl_parser.done(): break

    if not pyxl_parser.done():
        lines = ['<%s> at (line:%d)' % (tag_info['tag'], tag_info['row'])
                 for tag_info in pyxl_parser.open_tags]
        raise PyxlParseError('Unclosed Tags: %s' % ', '.join(lines))

    remainder = pyxl_parser.get_remainder()
    if remainder:
        tokens.rewind_and_retokenize(remainder)
        # Strip the remainder out from the last seen token
        if remainder[1]:
            last = seen[-1]
            seen[-1] = (last[0], last[1][:-len(remainder[1])], last[2], remainder[2], last[4])

    output = "html.PYXL('''{}''', {}, {}, {}{}{})".format(
        Untokenizer().untokenize(seen).replace('\\', '\\\\').replace("'", "\\'"),
        # Include the real compiled pyxl so that tools can see all the gritty details
        untokenize([pyxl_parser.get_token()]),
        # Include the start column so we can shift it if needed
        pyxl_parser.start[1],
        # Include the columns of each python fragment so we can shift them if needed
        ', '.join([str(get_start_column(x[0])) for x in python_stuff]),
        ', ' if python_stuff else '',
        # When untokenizing python fragments, make sure to place them in their
        # proper columns so that we don't detect a shift if there wasn't one.
        ', '.join([untokenize_with_column(x) for x in python_stuff]))
    return (tokenize.STRING, output, pyxl_parser.start, pyxl_parser.end, '')


def untokenize_with_column(tokens):
    """Untokenize a series of tokens, with it in its proper column.

    This requires inserting a newline before it.
    """
    tok_type, token, start, end, line = tokens[0]
    return Untokenizer(start[0] - 1, 0).untokenize(tokens)


def cleanup_tokens(tokens):
    last_nw_token = None
    prev_token = None

    while 1:
        try:
            token = next(tokens)
        except (StopIteration, tokenize.TokenError):
            break

        ttype, tvalue, tstart, tend, tline = token

        if ttype not in (tokenize.INDENT,
                         tokenize.DEDENT,
                         tokenize.NL,
                         tokenize.NEWLINE,
                         tokenize.COMMENT):
            last_nw_token = token

        # strip trailing newline from non newline tokens
        if tvalue and tvalue[-1] == '\n' and ttype not in (tokenize.NL, tokenize.NEWLINE):
            ltoken = list(token)
            tvalue = ltoken[1] = tvalue[:-1]
            token = tuple(ltoken)

        # tokenize has this bug where you can get line jumps without a newline token
        # we check and fix for that here by seeing if there was a line jump
        if prev_token:
            prev_ttype, prev_tvalue, prev_tstart, prev_tend, prev_tline = prev_token

            prev_row, prev_col = prev_tend
            cur_row, cur_col = tstart

            # check for a line jump without a newline token
            if (prev_row < cur_row and prev_ttype not in (tokenize.NEWLINE, tokenize.NL)):

                # tokenize also forgets \ continuations :(
                prev_line = prev_tline.strip()
                if prev_ttype != tokenize.COMMENT and prev_line and prev_line[-1] == '\\':
                    start_pos = (prev_row, prev_col)
                    end_pos = (prev_row, prev_col+1)
                    yield (tokenize.STRING, ' \\', start_pos, end_pos, prev_tline)
                    prev_col += 1

                start_pos = (prev_row, prev_col)
                end_pos = (prev_row, prev_col+1)
                yield (tokenize.NL, '\n', start_pos, end_pos, prev_tline)

        prev_token = token
        yield token


def try_fixing_indent(s, diff):
    """Given a string, try to fix its internal indentation"""
    if '\n' not in s:
        return s
    lines = s.split('\n')
    if len(lines) < 2:
        return s
    fixed = [lines[0]]
    spacing = " " * abs(diff)
    for line in lines[1:]:
        if diff > 0 and line:
            line = spacing + line
        elif diff < 0 and line.startswith(spacing):
            line = line[len(spacing):]
        fixed.append(line)

    return '\n'.join(fixed)

def untokenize(toks):
    return Untokenizer().untokenize(toks).strip()

def get_start_column(token):
    """From a token, get the starting column"""
    # ttype, tvalue, (tstartrow, tstartcol), tend, tline = token
    return token[2][1]

def get_end_column(token):
    """From a token, get the ending column"""
    # ttype, tvalue, tstart, (tendrow, tendcol), tend, tline = token
    return token[3][1]

def get_first_non_ws_token(tokens):
    for token in tokens:
        if token[0] not in (tokenize.INDENT,
                            tokenize.DEDENT,
                            tokenize.NL,
                            tokenize.NEWLINE):
            return token
    # well... let's return *something*
    return tokens[-1]


def reverse_tokens(tokens):
    saved_tokens = []

    curly_depth = 0

    in_pyxl = []
    start_depth = []
    arg_buffers_stack = []
    current_buffer_stack = []

    while 1:
        try:
            token = next(tokens)
        except (StopIteration, tokenize.TokenError):
            if in_pyxl:
                raise PyxlUnfinished
            break

        ttype, tvalue, tstart, tend, tline = token

        if ttype == tokenize.NAME and tvalue == 'html' and len(saved_tokens) == 0:
            saved_tokens.append(token)
            continue
        elif ttype == tokenize.OP and tvalue == '.' and len(saved_tokens) == 1:
            saved_tokens.append(token)
            continue
        elif ttype == tokenize.NAME and tvalue == 'PYXL' and len(saved_tokens) == 2:
            saved_tokens.append(token)
            continue
        if ttype == tokenize.OP and tvalue == '(' and len(saved_tokens) == 3:
            start_depth.append(curly_depth)
            curly_depth += 1
            in_pyxl.append(saved_tokens[0][2])
            saved_tokens = []
            current_buffer_stack.append([])
            arg_buffers_stack.append([])

            continue
        else:
            if in_pyxl:
                current_buffer_stack[-1].extend(saved_tokens)
            else:
                yield from saved_tokens
            saved_tokens = []

        if ttype == tokenize.OP and tvalue in '{([':
            curly_depth += 1
        if ttype == tokenize.OP and tvalue in '})]':
            curly_depth -= 1
            if in_pyxl and curly_depth == start_depth[-1]:
                pyxl_start = in_pyxl.pop()
                arg_buffers = arg_buffers_stack.pop()
                if current_buffer_stack[-1]:
                    arg_buffers.append(current_buffer_stack[-1])
                current_buffer_stack.pop()
                start_depth.pop()

                fmt_buffer, _, start_pos_buffer, *pos_and_arg_buffers = arg_buffers

                num_args = len(pos_and_arg_buffers)//2
                orig_pos_buffers = pos_and_arg_buffers[:num_args]
                real_arg_buffers = pos_and_arg_buffers[num_args:]

                orig_poses = [int(untokenize(x)) for x in orig_pos_buffers]
                real_poses = [get_start_column(get_first_non_ws_token(x))
                              for x in real_arg_buffers] # grab the columns...
                # Shift the indentation position of all of the arguments to the columns
                # they were at in the original source. (The final pyxl literal will then
                # be shifted from its original column to its new column.)
                args = [try_fixing_indent(untokenize(buf), orig_pos - real_pos)
                        for buf, orig_pos, real_pos
                        in zip(real_arg_buffers, orig_poses, real_poses)]

                # XXX escaping {s??
                fmt = ast.literal_eval(untokenize(fmt_buffer))
                orig_start_col = int(untokenize(start_pos_buffer))

                # print("CLOSED\n|{}|".format(fmt.format(*args)))

                # format to get the raw pyxl
                raw_pyxl = fmt.format(*args)
                # and then try to repair its internal indentation if the start position shifted
                fixed_pyxl = try_fixing_indent(raw_pyxl, pyxl_start[1] - orig_start_col)

                token = (tokenize.STRING, fixed_pyxl, pyxl_start, tend, '')

                if in_pyxl:
                    current_buffer_stack[-1].append(token)
                else:
                    yield token
                continue
            if curly_depth < 0:
                tokens.unshift(token)
                return

        if (in_pyxl and ttype == tokenize.OP and tvalue == ','
                and curly_depth == start_depth[-1] + 1):
            arg_buffers_stack[-1].append(current_buffer_stack[-1])
            current_buffer_stack[-1] = []
            continue
        elif in_pyxl:
            current_buffer_stack[-1].append(token)
            continue

        prev_token = token
        yield token
