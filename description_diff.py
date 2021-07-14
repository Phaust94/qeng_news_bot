from __future__ import annotations

from typing import List, Callable, Tuple, Union
import re
import difflib
import html
from itertools import zip_longest

import typing

Token = str
TokenList = List[Token]
whitespace = re.compile(r'\s+')
end_sentence = re.compile(r'[.!?\n]\s+')


def tokenize(s: str) -> TokenList:
    '''Split a string into tokens'''
    return whitespace.split(s)


def untokenize(ts: TokenList) -> str:
    '''Join a list of tokens into a string'''
    return ' '.join(ts)


def sentencize(s: str) -> TokenList:
    '''Split a string into a list of sentences'''
    return end_sentence.split(s)


def unsentencise(ts: TokenList) -> str:
    '''Join a list of sentences into a string'''
    return '. '.join(ts)


def html_unsentencise(ts: TokenList) -> str:
    '''Joing a list of sentences into HTML for display'''
    return ''.join(f'<p>{t}</p>' for t in ts)


def mark_text(text: str) -> str:
    return f'<span style="color: red;">{text}</span>'


def mark_span(text: TokenList) -> TokenList:
    if len(text) > 0:
        text[0] = '<span style="background: #69E2FB;">' + text[0]
        text[-1] += '</span>'
    return text


def align_seqs(a: TokenList, b: TokenList, fill: Token = '') -> Tuple[TokenList, TokenList]:
    out_a, out_b = [], []
    seqmatcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, a0, a1, b0, b1 in seqmatcher.get_opcodes():
        delta = (a1 - a0) - (b1 - b0)
        out_a += a[a0:a1] + [fill] * max(-delta, 0)
        out_b += b[b0:b1] + [fill] * max(delta, 0)
    assert len(out_a) == len(out_b)
    return out_a, out_b


def markup_diff(a: TokenList, b: TokenList,
                mark: Callable[[TokenList], TokenList] = mark_span,
                default_mark: Callable[[TokenList], TokenList] = lambda x: x,
                isjunk: Union[None, Callable[[Token], bool]] = None) -> Tuple[TokenList, TokenList]:
    """Returns a and b with any differences processed by mark

    Junk is ignored by the differ
    """
    seqmatcher = difflib.SequenceMatcher(isjunk=isjunk, a=a, b=b, autojunk=False)
    out_a, out_b = [], []
    for tag, a0, a1, b0, b1 in seqmatcher.get_opcodes():
        markup = default_mark if tag == 'equal' else mark
        out_a += markup(a[a0:a1])
        out_b += markup(b[b0:b1])
    assert len(out_a) == len(a)
    assert len(out_b) == len(b)
    return out_a, out_b


def html_sidebyside(
        a: typing.List[str], b: typing.List[str],
        a_name: str = None, b_name: str = None
):
    # Set the panel display
    out = '<div style="display: grid;grid-template-columns: 1fr 1fr;grid-gap: 1px;" id="main">'
    if a_name and b_name:
        out += f"<div><b>{a_name}</b></div><div><b>{b_name}</b></div>"
    # There's some CSS in Jupyter notebooks that makes the first pair unalign. This is a workaround
    # out += '<p></p><p></p>'
    for left, right in zip_longest(a, b, fillvalue=''):
        out += f'<div>{left}</div>'
        out += f'<div>{right}</div>'
    out += '</div>'
    return out


def html_diffs(a: str, b: str, a_name: str = None, b_name: str = None):
    a = html.escape(a)
    b = html.escape(b)

    out_a, out_b = [], []
    for sent_a, sent_b in zip(*align_seqs(sentencize(a), sentencize(b))):
        mark_a, mark_b = markup_diff(tokenize(sent_a), tokenize(sent_b))
        out_a.append(untokenize(mark_a))
        out_b.append(untokenize(mark_b))

    diff_html = html_sidebyside(out_a, out_b, a_name, b_name)
    return diff_html
