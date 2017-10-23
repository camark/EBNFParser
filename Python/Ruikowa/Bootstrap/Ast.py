#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 19 15:26:59 2017

@author: misakawa
"""
DEBUG = True
from ..ObjectRegex.Node import Ast
from ..Core.BaseDef import *
from .. import ErrorFamily
import re, os

# make escape string.
esc = lambda str: str.replace("'",r"\'").replace('"',r'\"')

def autoToken(info, LiteralParserInfo):

    prefix, value = LiteralParserInfo

    if prefix is 'R':  # Regex
        action = lambda:info['regex'].append("'{ESCAPED}'".format(ESCAPED=re.escape(value[1:-1])))
    elif prefix is 'L':  # Literal
        action = lambda:info['liter'].append("'{ESCAPED}'".format(ESCAPED=re.escape(value[1:-1])))
    elif prefix is Undef or prefix is 'K':  # Keyword
        action = lambda:info['keywd'].append(value)
    elif prefix is 'C':
        action = lambda:info['char'].append(value)
    else:
        raise UnsolvedError("Invalid Str Prefix {PREFIX}".format(PREFIX=value))

    if prefix is Undef or prefix is 'K' or prefix is 'L':
        lazy_define = lambda name=Undef:\
            ("{name} = LiteralParser({value}, name = '{name}')" \
            .format(name = name,
                    value = value) \
                if name else \
            "LiteralParser({value}, name='{ESC_STR}')"\
            .format(value=value,
                    ESC_STR = esc(value)))

    elif prefix is 'R':
        lazy_define = lambda name=Undef:\
            ("{name} = LiteralParser({value}, name = '{name}', isRegex = True)" \
             .format(name=name,
                     value=value) \
                 if name else \
            "LiteralParser({value}, name='{ESC_STR}', isRegex = True)" \
             .format(value=value,
                     ESC_STR=esc(value)))

    elif prefix is 'C':
        lazy_define = lambda name=Undef:\
            ("{name} = CharParser({value}, name = '{name}')" \
             .format(name=name,
                     value=value) \
                 if name else \
            "CharParser({value}, name='{ESC_STR}')" \
             .format(value=value,
                     ESC_STR=esc(value)))

    return lazy_define, action


def ast_for_stmts(stmts : Ast, info = Undef):
    if info is Undef:
        info = dict(keywd = [], regex = [], liter = [])

    assert stmts.name == 'Stmt'
    res = []   
    to_compile= []
    codesDefToken = Undef
    DefTokenInEBNF= True

    if stmts[0].name is 'TokenDef':
        """ 
            TokenDef[
                    'Token'
                    (Codes|Name)
                    ] 
        """
        usingType:str =  stmts[0][1]
        if usingType.startswith('{{'):
            codesDefToken = stmts[0][1][2:-2]
        else:
            path = os.path.join(*filter(lambda x:x,  usingType.split('.')))

            with open("./{path}".format(path = path)) as read_from:
                codesDefToken = read_from.read()
        DefTokenInEBNF    = False      
        stmts.reverse();stmts.pop();stmts.reverse()

    for eq in stmts:
        define, action = ast_for_equal(eq, info)

        if action is Undef:
            # so it's an AstParser.
            to_compile.append(eq[0])

        elif DefTokenInEBNF:
            action()

        res.append(define)

    tks = info if DefTokenInEBNF else codesDefToken

    return res, tks, to_compile
              
           
#     groupBy(lambda x : )


def ast_for_equal(eq : Ast, info):
    assert eq.name == 'Equals'
    case = eq[1]
    name = eq[0]
    if case == ':=':
        value = eq[2]

        if not value.startswith('\''):
            prefix = value[0]
            value  = value[1:]
        else:
            prefix = Undef

        lazy_define, action = autoToken(info, (prefix, value))
        return lazy_define(name), action


    else:
        toIgnore = Undef
        if isinstance(case, Ast):
            toIgnore = case[2:-1]
        value = ast_for_expr(eq[-1], info)
        if toIgnore is Undef:
            return "{name} = AstParser({DEFINITIONS}, name = '{name}')"\
                    .format(name = name,
                            DEFINITIONS=','.join(value)
                    ), Undef

        else:
            toIgnore = [{ignore
                        for ignore in toIgnore if not ignore.startswith('\'')
                        },
                        {ignore
                        for ignore in toIgnore if    ignore.startswith('\'')
                        }]
            return "{name} = AstParser({DEFINITIONS}, name = '{name}', toIgnore = {toIgnore})" \
                   .format(name=name,
                           DEFINITIONS=','.join(value),
                           toIgnore  = toIgnore
                    ), Undef
            
    
def ast_for_expr(expr : Ast, info):
    return [ast_for_or(or_expr, info) for or_expr in expr if or_expr is not '|']

def ast_for_or(or_expr : Ast, info):
    return '[{res}]'.format(res = ','.join(ast_for_atomExpr(atomExpr, info) for atomExpr in or_expr))

def ast_for_atomExpr(atomExpr : Ast, info):
    
    res =  ast_for_atom(atomExpr[0], info)

    if len(atomExpr) is 2:

        case = atomExpr[1][0]

        if   case is '*':
            res = ast_for_trailer('[{res}]'.format(res = res), info)
        elif case is '+':
            res = ast_for_trailer('[{res}]'.format(res = res), atleast = 1, info = info)
        elif case is '{':
            atleast = atomExpr[1][1]
            case    = atomExpr[1][2]
            if case is '}':
                res = ast_for_trailer('[{res}]'.format(res = res),
                                      atleast = atleast,
                                      info = info)
            else:
                atmost = case
                res = ast_for_trailer('[{res}]'.format(res = res),
                                      atleast = atleast,
                                      atmost = atmost,
                                      info = info)
    return res

def ast_for_atom(atom : Ast, info):
    n = len(atom)
    if n is 1:
        liter:str = atom[0]
        if isinstance(liter, Ast):
            """
            R'target' | 'target' | C'\n' | C 'c'
            =>
            regex       keyword    single-char
            """
            assert  liter.name == 'AstStr'
            string = liter[0]
            LiteralParserInfo = Undef
            if not string.startswith('\''):
                prefix = string[0]
                string = string[1:]
            else:
                prefix = Undef

            lazy_define, action = autoToken(info, (prefix, string))
            action()
            return lazy_define()

        else:
            return "Ref('{Name}')".format(Name=liter)

    else:
        if DEBUG:
            assert n is 3
        case = atom[0]
        if   case is '[':
            return ast_for_trailer("{DEFINITIONS}"\
                                        .format(DEFINITIONS = ','.join(ast_for_expr(atom[1], info = info))),
                                   atleast = 0,
                                   atmost = 1,
                                   info = info)
        elif case is '(':
            or_exprs = ast_for_expr(atom[1], info = info)
            if len(or_exprs) is 1:
                return or_exprs[0][1:-1]
            return ast_for_trailer("{DEFINITIONS}"\
                                        .format(DEFINITIONS=','.join(or_exprs)),
                                   atleast = 1,
                                   atmost = 1,
                                   info = info)
        else:
            ErrorFamily.UnsolvedError("Unsolved Atom Parsed Ast.")


def ast_for_trailer(series_expr, info, atleast = 0, atmost = None):
    if atleast is 0:
        if atmost is None:
            return "SeqParser({series_expr})"\
                .format(series_expr = series_expr)
        else:
            return "SeqParser({series_expr}, atmost = {atmost})"\
                .format(series_expr=series_expr, atmost = atmost)
    else:
        if atmost is Undef:
            return "SeqParser({series_expr}, atleast = {atleast})"\
                .format(series_expr=series_expr,atleast=atleast)
        else:
            return "SeqParser({series_expr}, atleast = {atleast}, atmost = {atmost})"\
                .format(series_expr=series_expr,atleast=atleast,atmost=atmost)

