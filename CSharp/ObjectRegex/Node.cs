#define DEBUG
using System.Text.RegularExpressions;
using System;
using System.Runtime.Serialization;
using System.Collections;
using System.Collections.Generic;
using System.Linq;

namespace CSharp.ObjectRegex
{
    

    public class ObjRegexError : Exception
    {
        public ObjRegexError(string info) : base(info)
        {
        }
        
    }
    public class StackOverFlowError: Exception{
        public StackOverFlowError(string info) : base(info)
        {
        }
    }

    public class NameError: Exception{
        public NameError(string info) : base(info)
        {
        }
    }

    public class CompileError: Exception{
        public CompileError(string info) : base(info)
        {
        }
    }
    public class RegexTool{
         
        public static Tuple<string, Func<string, string>> reMatch(string a, bool escape = false){
            var token_rule = escape?Regex.Escape(a):a;
        
            var re_        = new Regex( token_rule );
           
            return new Tuple<string, Func<string, string>>
                    (token_rule,
                     (string str)=>{
                        if (str.Length==0)
                            return null;
                        var r = re_.Match(str);
                        if (r.Index !=0)
                            throw new ObjRegexError("empty tokenized word.");
                        if (r.Length!=str.Length)
                            return null;
                        return str;
                        }
                    );
        } 
    } 
    public class Mode :List<Mode>{
        
        
        public string name = null;
        public string value= null;
    
        public Mode setName(string name){
            this.name = name;
            return this;
        } 
        public Mode setValue(string value){
            this.value = value;
            return this;
        }
  
        public string Dump(int i=0){
            var space = "\n"+new String(' ', i);
            var toDump = string.Join("", 
                this.Select(
                    mode =>{
                        if (mode.value != null){
                            if (mode.value.Equals("\n")){
                                return $"{mode.name}[{@"\n"}]";
                            }
                            return $"{mode.name}[{mode.value}]";
                        }
                        else{
                            
                            return mode.Dump(i+1);
                        }
                            
                    }
            ));
            return $"{this.name}[{toDump+space}]";
        }
    }

    public class MetaInfo{
        public int count = 0;
        public int rdx = 0;

        public int trace_length = 0;
        public int history_length = 0;
        public Stack<(int, string)> trace  = null;
            

        public Stack<(int,int,int)> history = null;

        protected (int, string) tracePop(){
            --trace_length;
            return trace.Pop();
        }

        public void traceAppend((int, string) tp){
            ++trace_length;
            trace.Append(tp);
        }

        protected (int, int, int) historyPop(){
            --history_length;
            return history.Pop();
        }

        protected void historyAppend((int, int, int) tp){
            ++history_length;
            history.Append(tp);
        }

        public MetaInfo(int count = 0, int rdx = 0, Stack<(int, string)> trace = null){
            this.count   = count;
            this.rdx     = rdx;

            if (trace ==null )
            {
                this.trace = new Stack<(int, string)>();
            }
            else{
                this.trace = trace;
                foreach(var i in trace)
                {
                    ++this.trace_length;            
                }
            }

            this.history = new Stack<(int,int,int)>();
        }
        public MetaInfo branch (){           
            historyAppend((count, rdx, trace_length)); 
            return this;
        }
        public MetaInfo rollback(){
            if (history_length == 0){
                throw new StackOverFlowError("Pull nothing.");
            }
            int trace_length;
            (this.count, this.rdx, trace_length) = historyPop();
            while (trace_length != this.trace_length){
                tracePop();
            }
            return this;
        }
        public MetaInfo pull(){
            if (history_length == 0){
                throw new StackOverFlowError("Pull nothing.");
            }
            historyPop();            
            return this;
        }
        public string DumpTrace(){
            return String.Join(" ", 
                trace.Select((a, b)=> $"({a}, {b})")
            );
        }
    };

    public abstract class BaseAst{
        public string name;
        public bool   has_recur;

        public abstract Mode Match(string[] objs, MetaInfo meta = null, bool partial = true);

    }

    public class LazyDef :BaseAst{

        public override Mode Match(string[] objs, MetaInfo meta = null, bool partial = true){
                throw new  CompileError($"Ast {this.name} Not compiled!");
        }
    
    }
    public class Liter : BaseAst{
        public string token_rule;

        public Func<string, string> f;


        public Liter(string i, string name = null, bool escape = false ){

            var (token_rule, f) = RegexTool.reMatch(i, escape);
            this.name = name;
            this.has_recur = false;
            this.token_rule = token_rule;
            this.f = f;
        }
        public override Mode Match(string[] objs, MetaInfo meta = null, bool partial = true){
            if (meta==null){
                meta = new MetaInfo();
            }
            int left = objs.Length - meta.count ;
            if (left==0) return null;
            var r = f(objs[meta.count]);  
            if ( r == null || ( (!partial)&&(left !=1 ))){
                    return null;
            }
            if (r == "\n")
                meta.rdx += 1;
            meta.count += 1;
            return new Mode().setName(this.name).setValue(r);
        }
        public Liter ELiter(string i, string name = null){
            
            return new Liter(i, name, true);
        }
    }
    class Ast : BaseAst{
        public List<List<BaseAst>> possibilities; 
        protected BaseAst[][] cache;
        protected Dictionary<string, Ast> compile_closure;
        bool compiled ;

        public Ast(Dictionary<string, Ast> compile_closure,
                   string name = null,
                   params BaseAst[][] ebnf){
            if (name == null)
                throw new NameError("Name not found! Each kind of ast should have a identity name.");
            cache = ebnf;
            if (compile_closure.Keys.Contains(name)){
                throw new NameError("Name of Ast should be identified!");
            }
            compile_closure[name] = this;
            compiled = false;
            this.compile_closure = compile_closure;
            possibilities = new List<List<BaseAst>>();
        }

        public Ast compile(HashSet<string> recur_searcher=null){

            if (recur_searcher == null){
                recur_searcher = new HashSet<string>();
                recur_searcher.Append(name);
            }
            else{
                if (recur_searcher.Contains(name)){
                    has_recur = true;
                }
                else{
                    recur_searcher.Append(name);
                }
            }

            if (compiled) 
                return this; 

            foreach(var es in cache){
                var possibility = new List<BaseAst>();
                possibilities.Append(possibility);
                foreach(var e in es){
                    if(e is LazyDef){
                        Ast refered = compile_closure[e.name];
                        possibility.Append(refered.compiled ? refered : refered.compile(recur_searcher: recur_searcher));
                    }
                    else if(e is Ast || e is Liter)
                        possibility.Append(e);
                }
            }
            cache = null;
            compiled = true;
            return this;
        }

        public override Mode Match(string[] objs, MetaInfo meta = null, bool partial = true){
            if (meta == null){
                meta = new MetaInfo();
            }
            #if DEBUG
                Console.WriteLine($"{this.name} WITH {meta.DumpTrace()}");
            #endif
            var res     = new Mode().setName(name);
            var has_res = false; 
            foreach(var possibility in possibilities){
                meta.branch();
                foreach(var thing in possibility){
                    var history = (meta.count, thing.name);
                    Mode r;
                    if (thing.has_recur){
                        if (meta.trace.Contains(history)){
                            Console.WriteLine("Found Left Recursion. Dealed.");
                            r = null;
                        }
                        else{
                            meta.trace.Append(history);
                            r = thing.Match(objs, meta, true);
                        }
                    }
                    else{
                        // DEBUG View
                        meta.trace.Append(history);
                        r = thing.Match(objs, meta, true);
                    }

                    if (r == null){
                        res.Clear();
                        meta.rollback();
                        goto ContinueForNewPossibility;
                    }
                    if (thing is Seq){
                        res.AddRange(r);
                    }
                    else{
                        res.Append(r);
                    }
                    #if DEBUG
                        Console.WriteLine($"{thing.name} <= {r.Dump()}");
                    #endif
                }
                #if DEBUG
                    Console.WriteLine($"RETURN from {this.name} ");
                #endif
                has_res = true;
                break;
                ContinueForNewPossibility:;
            }
            if (!has_res){
                #if DEBUG
                    Console.WriteLine($"RETURN None from {this.name} ");
                #endif
                return null;
            }
            meta.pull();
            var left = objs.Length -meta.count;
            if (partial || left == 0){
                #if DEBUG
                    Console.WriteLine($"RETURN Some from {this.name}");
                #endif
                return res;
            }
            #if DEBUG
                Console.WriteLine($"RETURN None from {this.name} (No partial and do not match all)");
            #endif
            return null;
        }
    }
    class Seq : Ast{
        int atleast;
        int atmost ;
        public Seq(Dictionary<string, Ast> compile_closure,
                   string name = null,
                   int atleast =   1,
                   int atmost  =  -1,
                   params BaseAst[][] ebnf):base(compile_closure, name, ebnf){
        this.atleast = atleast;
        this.atmost  = atmost;
        }

        public override Mode Match(string[] objs, MetaInfo meta = null, bool partial = true){
            if (meta == null){
                meta = new MetaInfo();
            }
            var res  = new Mode().setName(this.name);
            int left = objs.Length - meta.count;
            if (left == 0){
                return atleast==0?res : null;
            } 
            meta.branch();
            Mode r;
            int idx = 0;
            if (atmost>0){
                while (true){
                    if (idx>=atmost) break;
                    r = base.Match(objs, meta, true);
                    if (r == null)
                        break;
                    res.AddRange(r);
                    ++idx;
                }
            }
            else{
                while (true){
                    r = base.Match(objs, meta, true);
                    if (r == null) break;
                    res.AddRange(r);
                    ++idx;
                }
            }
            #if DEBUG
                Console.WriteLine($"{name} <= {res.Dump()}");
            #endif
            if (idx<atleast){
                meta.rollback();
                return null;
            }
            meta.pull();
            return res; 
        }
    }
}