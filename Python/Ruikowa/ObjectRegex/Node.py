#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 18:53:53 2017

@author: misakawa
"""


DEBUG = True

from ..Core.BaseDef import *
from .MetaInfo import MetaInfo
from ..ErrorFamily import *
from .PatternMatching import *
from collections import deque

class Ast(deque):
    def __init__(self, name:str):
        super(Ast, self).__init__()
        self.name = name

class Ignore:
    Value = 0
    Name  = 1

class BaseParser:
    """Abstract Class"""
    name       = Undef
    has_recur  = Undef
    def match(self, objs:List[str], meta:MetaInfo, allowLR:bool):
        """Abstract Method"""
        raise Exception("There is no access to an abstract method.")
        # incomplete

class CharParser(BaseParser):
    """
    To parse the single character.
    """
    def __init__(self, mode:str):
        length = len(mode)
        assert length is 1 or (length is 2 and mode[0] == '\\')
        self.mode  = mode
        self.name  = "'{MODE}'".format(MODE=mode)
        self.match = Match_Char_By(self)

class LiteralParser(BaseParser):
    """
    To parse the literal.
    """
    def __init__(self, mode:str,
                       name:str,
                       isRegex:bool = False,
                       ifIsRegexThenEscape:bool=True):
        self.name = name
        self.isRegex = isRegex
        if isRegex:
            self.mode  = Generate_RegexPatten_From(mode, escape=ifIsRegexThenEscape)
            self.match = Match_With_Regex_By(self)
        else:
            self.mode  = mode
            self.match = Match_Without_Regex_By(self)

    def RawFormDealer(rawStr, name):
        return LiteralParser(rawStr, name = name, isRegex = False)

class Ref(BaseParser):
    def __init__(self,name):self.name = name

class AstParser(BaseParser):
    def __init__(self, *ebnf, name=None, toIgnore: List[set] = None):
        # each in the cache will be processed into a parser.
        self.cache = ebnf

        # the possible output types for an series of input tokenized words.
        self.possibilities = []

        # whether this parser will refer to itself.
        self.has_recur = False

        # the identity of a parser.

        self.name = name if name is not None else \
            ' | '.join(' '.join(map(lambda parser: parser.name, ebnf_i)) for ebnf_i in ebnf)

        # is this parser compiled, must be False when initializing.
        self.compiled = False

        #  if a parser's name is in this set, the result it output will be ignored when parsing.
        self.toIgnore = toIgnore




    def compile(self, namespace: dict, recurSearcher: set):
        if self.name:
            if self.name in recurSearcher:
                self.has_recur = True
                self.compiled = True
            else:
                recurSearcher.add(self.name)
        if self.compiled: return self
        self.patternMatch = patternMatch(self)
        if isinstance(self, SeqParser):
            self.matchOne = AstMatch(self)
        else:
            self.match    = AstMatch(self)

        for es in self.cache:
            self.possibilities.append([])
            for e in es:
                if   isinstance(e, LiteralParser) or \
                     isinstance(e, CharParser   ):
                     self.possibilities[-1].append(e)

                elif isinstance(e, Ref):
                     e = namespace[e.name]
                     if isinstance(e, AstParser):
                        e.compile(namespace, recurSearcher)
                     self.possibilities[-1].append(e)
                     if e.has_recur:
                        self.has_recur = True

                elif isinstance(e, AstParser):

                     if e.name not in namespace:
                        namespace[e.name] = e
                     else:
                        e = namespace[e.name]
                     e.compile(namespace, recurSearcher)
                     self.possibilities[-1].append(e)
                     if e.has_recur:
                        self.has_recur = True
                else:
                     raise UnsolvedError("Unknown Parser Type.")

        if hasattr(self, 'cache'):
            del self.cache

        if not self.compiled: self.compiled = True

def AstMatch(self):
    def match(objs:List[str], meta:MetaInfo, allowLR:bool = True):

        if self.has_recur:

            if self not in meta.trace[meta.count][:meta.trace[meta.count].length]:
                print('LENGTH BEFORE:', meta.trace[meta.count].length)
                meta.trace[meta.count].push(self)
                print('LENGTH BEFORE:', meta.trace[meta.count].length)
            else:
                if not allowLR:
                    return Const.UnMatched
                raise RecursiveFound(self)

        for possibility in self.possibilities:
            meta.branch()
            result = self.patternMatch(objs, meta, possibility, allowLR = allowLR)

            if result is Const.UnMatched:
                meta.rollback()
                continue

            elif isinstance(result, Ast):
                meta.pull()
                return result

            elif isinstance(result, RecursiveFound):
                if self is result.node:
                    print("RECUR DEAL AT ", self.name)
                    meta.pull()
                    break # Deal (Cycle) Left Recursive Cases
                else:
                    print("RECUR PASS BY ", self.name)
                    meta.rollback()  # rollback or pull?
                    return result

        else:
            meta.rollback()
            return Const.UnMatched

        # if LR :
        print(result)
        result:RecursiveFound
        veryFirst = result.node.match(objs, meta, allowLR=False)
        first = veryFirst
        if first is Const.UnMatched:
            return Const.UnMatched

        # do left recur :
        while True:
            meta.branch()
            for parser, possibility in result.possibilities:
                result : Ast= parser.patternMatch(objs, meta, possibility)
                if result is Const.UnMatched:
                    meta.rollback()
                    return veryFirst
                result.appendleft(first)
                first = result
            meta.pull()
            veryFirst = first

        # unexpected end.
        raise UnsolvedError("unexpected LR!!!")

    return match


def patternMatch(self:AstParser):
    def subMatch(
             objs:List[str],
             meta:MetaInfo ,
             possibility:List[BaseParser],
             allowLR:bool = True):


        try: # Not recur
            result = Ast(self.name)
            for parser in possibility:

                r = parser.match(objs, meta = meta, allowLR = True if result else allowLR)
                # if `result` is still empty, it might not allow LR now.

                if isinstance(r, str) or isinstance(r, Ast):

                    if isinstance(parser, SeqParser):
                        result.extend(r)
                    else:
                        result.append(r)


                elif r is Const.UnMatched:
                    return Contrl.UnMatched

                elif isinstance(r, RecursiveFound):
                    if DEBUG:
                        print('Recur ADD ', r)
                    r.add((self, possibility[possibility.index(parser)+1:]) )
                    return r

            else:
                return result

        except RecursiveFound as RecurInfo:
            print("Found \n", RecurInfo)
            RecurInfo.add((self, possibility[possibility.index(parser)+1:]))
            # RecurInfo has a trace of Beginning Recur Node to Next Recur Node with
            # specific possibility.
            return RecurInfo

    return subMatch

class SeqParser(AstParser):
    def __init__(self, *ebnf, name=Undef, atleast=0, atmost=Undef):
        super(SeqParser, self).__init__(*ebnf, name = name)

        if atmost is Undef:
            if atleast is 0:
                self.name = "({NAME})*".format(NAME = self.name)
            else:
                self.name = '({NAME}){{{AT_LEAST}}}'.format(NAME = self.name, AT_LEAST=atleast)
        else:
            self.name = "({NAME}){{{AT_LEAST},{AT_MOST}}}".format(
                                                                NAME =self.name,
                                                                AT_LEAST=atleast,
                                                                AT_MOST =atmost)
        self.atleast = atleast
        self.atmost  = atmost

    def match(self, objs:List[str], meta:MetaInfo, allowLR:bool=True):
        result = Ast(self.name)

        if meta.count == len(objs):  # boundary cases
            if self.atleast is 0:
                return result
            return Const.UnMatched

        meta.branch()
        idx = 0
        if self.atmost is not Undef:
            """ (ast){a b} """
            while True:
                if idx >= self.atmost:
                    break
                try:
                    r = self.matchOne(objs, meta=meta)
                except IndexError:
                    break

                if r is Const.UnMatched:
                    break
                elif isinstance(r, RecursiveFound):
                    meta.rollback()
                    return Const.UnMatched

                result.extend(r)
                idx += 1
        else:
            """ ast{a} | [ast] | ast* """
            while True:

                try:
                    r = self.matchOne(objs, meta=meta)
                except IndexError:
                    break

                if r is Const.UnMatched:
                    break
                result.extend(r)
                idx += 1
        if DEBUG:
            print(f'idx => {idx}')
        if  idx < self.atleast:
            meta.rollback()
            return Const.UnMatched
        meta.pull()
        return result






    # if not SndNodeOfRecur : NoRecur = True

















