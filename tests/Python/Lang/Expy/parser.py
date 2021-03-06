
from Misakawa.ObjectRegex.Node import Ref, AstParser, SeqParser, LiteralParser, MetaInfo
from etoken import token 
import re
namespace     = globals()
recurSearcher = set()
Stmt = AstParser([SeqParser([SeqParser([Ref('NEWLINE')]),SeqParser([Ref('Expr')]),SeqParser([Ref('NEWLINE')])])], name = 'Stmt')
Expr = AstParser([Ref('BinOp')],[Ref('Factor')], name = 'Expr')
BinOp = AstParser([Ref('Factor'),SeqParser([Ref('Op'),Ref('Factor')])], name = 'BinOp')
Factor = AstParser([SeqParser([Ref('Op')]),Ref('AtomExpr')], name = 'Factor')
AtomExpr = AstParser([SeqParser([Ref('Closure')],[Ref('Atom')], atleast = 1, atmost = 1),SeqParser([SeqParser([LiteralParser.Eliteral('[', name = '\'[\''),SeqParser([Ref('Expr')]),LiteralParser.Eliteral(']', name = '\']\'')],[LiteralParser.Eliteral('(', name = '\'(\''),SeqParser([Ref('Expr')]),LiteralParser.Eliteral(')', name = '\')\'')],[LiteralParser.Eliteral('.', name = '\'.\''),Ref('Name')], atleast = 1, atmost = 1)])], name = 'AtomExpr')
Atom = AstParser([Ref('Const')],[Ref('Str')],[Ref('Name')],[Ref('Number')],[LiteralParser.Eliteral('[', name = '\'[\''),SeqParser([Ref('Expr')]),LiteralParser.Eliteral(']', name = '\']\'')],[LiteralParser.Eliteral('(', name = '\'(\''),SeqParser([Ref('Expr'),SeqParser([LiteralParser.Eliteral(',', name = '\',\''),SeqParser([Ref('Expr'),SeqParser([LiteralParser.Eliteral(',', name = '\',\''),Ref('Expr')])], atmost = 1)], atmost = 1)], atmost = 1),LiteralParser.Eliteral(')', name = '\')\'')], name = 'Atom')
Closure = AstParser([LiteralParser.Eliteral('{', name = '\'{\''),SeqParser([Ref('Expr'),SeqParser([Ref('NEWLINE')])]),LiteralParser.Eliteral('}', name = '\'}\'')],[LiteralParser('def(?!\S)', name = '\'def(?!\S)\''),SeqParser([Ref('Name')], atmost = 1),LiteralParser.Eliteral('(', name = '\'(\''),Ref('tpdef'),LiteralParser.Eliteral(')', name = '\')\''),Ref('Closure')], name = 'Closure')
tpdef = AstParser([SeqParser([Ref('Name')])], name = 'tpdef')
Op = LiteralParser('\/\/|\/|\|\||\||\>\>|\<\<|\>\=|\<\=|\<\-|\>|\<|\=\>|\-\>|\?|\-\-|\+\+|\*\*|\+|\-|\*|\=\=|\=|\~|\@|\$|\%|\^|\&|\!|\:\:|\:', name = 'Op')
Number = LiteralParser('\d+|\d*\.\d+', name = 'Number')
Const = LiteralParser('True(?!\S)|False(?!\S)|None(?!\S)', name = 'Const')
Str = LiteralParser('[a-z]{0,1}"[\w|\W]*"', name = 'Str')
Name = LiteralParser('[a-zA-Z_][a-zA-Z0-9]*', name = 'Name')
NEWLINE = LiteralParser('\n', name = 'NEWLINE')
Stmt.compile(namespace, recurSearcher)
Expr.compile(namespace, recurSearcher)
BinOp.compile(namespace, recurSearcher)
Factor.compile(namespace, recurSearcher)
AtomExpr.compile(namespace, recurSearcher)
Atom.compile(namespace, recurSearcher)
Closure.compile(namespace, recurSearcher)
tpdef.compile(namespace, recurSearcher)
