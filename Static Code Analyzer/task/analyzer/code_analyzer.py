import re
import operator
import sys
import os
import ast


lst_code = ["   This should give error S002",
            "    This should be fine",
           "This is an error S003;",
            "  # This is not an error S003",
           r"'''This not an error S0003;'''",
            r'"""This is not an error S003;"""',
           "function(a, b) # This is an error S004",
           "function(a, b)  # This is not an error S004",
           "'''This is a multiline",
           "comment;",
           "that spans 3 lines. No errors here;'''",
           "todo_todito() # nothing wrong here",
           "print('todo')",
           "function()  # TODO this is error",
           "function()# #todo this is error",
           """todo todo todo, es tuyo si querés""",
           "'''this is todo a multiline,",
           "with a second line todo and",
           "with a third line todo'''",
           "TODO()",
            "",
            "",
            "",
            "   code #  #    #",
            "code  # # #",
            "print('hello'); # inline comment",
            "def function_tu_vieja(Variable1, variable_numero_2=True, *ArGs, **kWargs):"
            "    a = 0",
            "    print('hello ', a)",
]

lst_code2 = ["def function_tu_vieja(Variable1, variable_numero_2=True, var_3=[], var4=3, var5='bleh', var6 = {}, *ArGs, **KwArgs):\n",
            "    print('hello')\n",
            "    a = 1\n",
            "    c = b = 2 * a\n",
            "    a = c\n",
            "    print(a, b, c)\n",
            "def FunctionCamelWrong():\n",
            "    pass\n",
             "def function_wrong_default(a={}):\n",
             "    pass\n"
             ]

error_desc = {"S001": "Too long",
              "S002": "Indentation is not a multiple of four",
              "S003": "Unnecessary semicolon after a statement",
              "S004": "Less than two spaces before inline comments",
              "S005": "TODO found",
              "S006": "More than two blank lines preceding a code line",
              "S007": "Too many spaces after 'const_name'",
              "S008": "Class name 'cl_name' should be written in CamelCase",
              "S009": "Function name 'fn_name' should be written in snake_case",
              "S010": "Argument name 'arg_name' should be written in snake_case",
              "S011": "Variable 'var_name' should be written in snake_case",
              "S012": "The default argument value is mutable"
              }


def get_comments(lines):
    """Return three lists of classifications of lines.
     The first list contains the tuples with beginning and end line numbers of multiline comments,
    another list with single line comments written between triple 'single' or "double" quotes and
    finally, last line of the multiline comments is added to a different list
    (a semicolon at the end of that line is an error too)."""
    multi_line = list()
    one_line = list()
    last_lines = list()
    ml_on = False
    for i, line in enumerate(lines):
        matches = re.findall(r"(\"\"\")|(\'\'\')", line.strip())
        if matches:
            if len(matches) == 1:  # multiline beginning or ending
                if not ml_on:
                    ini = i
                else:
                    end = i
                    multi_line.extend([j for j in range(ini, end)])
                    last_lines.append(end)
                ml_on = not ml_on
            elif len(matches) == 2 and len(set(matches)) == 1:  # a pair of """ or '''
                one_line.append(i)
    return multi_line, last_lines, one_line


def get_inline_comment(line):
    """ Return the inline comment, whether it is a
        hashtag single line comment
        or an inline comment to the right of the code
    """
    try:
        comment = ''.join(line.split("#")[1:])
        return comment
    except Exception:
        return ""


def is_blankline(line):
    return line.strip() == ""


def is_hashtag_comment_line(line):
    try:
        return line.strip()[0] == "#"
    except Exception:
        return ""


def classify_lines(codelines):
    """ Classify all the lines in the code and return a dictionary with type of line as keys and sets of line numbers as
    values. Additional classifications that are combinations of the most elemental are added for convenience.
    Possible types of lines: "multiline comment", "multiline comment last line", "single line comment",
    "blankline", "code without comment", "code with inline comment" (written in singular)
    Additional types: "comment_quoted" (multiline and single line comments between 3 double or single quote pairs),
    "semicolon_exceptions" (single line comment with hashtag + multiline comments except last line),
    "code_lines" (all lines of code, with or without inline comment),
    "comments" (comment lines: multiple line or single line comments. Does not include inline comments).

    Args:
        codelines: a list with the lines of code

    Returns:
        a dictionary where they keys are the classification and the values are the line numbers.
    """

    types = ["multiline_comment_not_last_line", "multiline_comment_last_line",
             "single_line_comment_quoted", "single_line_comment_hashtag",
             "blank_line", "code_without_comment", "code_with_inline_comment"]

    dic = {key: list() for key in types}
    mc, ll, olc = get_comments(codelines)
    dic["multiline_comment_not_last_line"] = mc
    dic["multiline_comment_last_line"] = ll
    dic["single_line_comment_quoted"] = olc
    dic["comment_quoted"] = mc + ll + olc
    for n, line_ in enumerate(codelines):
        if n not in dic["comment_quoted"]:
            if is_hashtag_comment_line(line_):
                dic["single_line_comment_hashtag"].append(n)
            elif is_blankline(line_):
                dic["blank_line"].append(n)
            elif get_inline_comment(line_):
                dic["code_with_inline_comment"].append(n)
            else:
                dic["code_without_comment"].append(n)

    # useful additional more general types:
    dic["semicolon_exceptions"] = dic["multiline_comment_not_last_line"] + dic["single_line_comment_hashtag"]
    dic["code_lines"] = dic["code_without_comment"] + dic["code_with_inline_comment"]
    dic["comments"] = dic["comment_quoted"] + dic["single_line_comment_hashtag"]

    return dic


def count_blank_lines(n, dic):
    """Count number of blank lines before the given line"""
    n -= 1
    count = 0
    while n in dic["blank_line"]:
        count += 1
        n -= 1
    return count


# Stage 3/5 Working with several files
def get_files(path):
    """returns a list of valid code files,accessible and ending with .py"""
    fs = []
    if os.path.isfile(path):
        fs.append(path)
    elif os.path.isdir(path):
        for root, dirs, files_ in os.walk(path, topdown=False):
            for name in files_:
                fs.append(os.path.join(root, name))
    # filter .py files and accesible
    filt_files = [file for file in fs
                  if (file[-3:] == ".py")
                  and os.access(file, os.F_OK)
                  and os.access(file, os.R_OK)]
    filt_files.sort()
    return filt_files


def read_file(file_path):
    with open(file_path, "r") as codefile:
        lst_code = codefile.readlines()
    return lst_code


def add_error(dic, n_line, n_error, **kwargs):
    """Return the same dictionary with the line and error added"""
    dic[n_line] = dic.setdefault(n_line, {})
    dic[n_line].setdefault(n_error, {})
    for key, value in kwargs.items():
        dic[n_line][n_error].setdefault(key, [])
        dic[n_line][n_error][key].append(value)
    return dic


def print_errors(dic_errors_sorted, error_desc, filename):
    for line, errors in dic_errors_sorted.items():
        for error, error_args in errors.items():
            if error_args:
                for key, values in error_args.items():
                    for value in values:
                        err_desc = error_desc[error]
                        err_desc = err_desc.replace(key, value)
                        print(f'{filename}: Line {line + 1}: {error} {err_desc}')
            else:
                err_desc = error_desc[error]
                print(f'{filename}: Line {line+1}: {error} {err_desc}')


#Stage 4/5: Checking class and function names
def get_construction(line):
    """return constructor type, number of spaces after constructor and contruction name"""
    m = re.match("(def|class)( +)([\\w_]+)(\\(.*\\))?:", line.strip())
    if m is not None:
        return str(m.group(1)), len(m.group(2)), str(m.group(3))
    else:
        return None, None, None


def is_camel_case(name):
    """Return True if CamelCase.
    CamelCase has no hyphens and one (the first) or more capital letters"""
    return (name.find("_") == -1) and (name[0].isupper())


def is_snake_case(name):
    # snake case is lowercase and might have hyphens
    return name == name.lower()


# Stage 5/5: Usage of AST. Checking variable names and arguments
def get_names_args(*args):
    var_names = []
    for arg in args:
        if type(arg) is list:
            for a in arg:
                var_names.append(a.arg)
        elif isinstance(arg, ast.arg):
            var_names.append(arg.arg)
    return var_names


def get_defaults(*defaults):
    default_list = []
    for lst in defaults:
        for default in lst:
            if isinstance(default, ast.Constant):
                default_list.append(default.value)
            else:
                default_list.append("#mutable")
    return default_list



def get_funcdef_node_data(n):
    """Return args and defaults from a function header and local variables from its body."""
    # get the local variables
    local_vars = {}
    for m in n.body:
        if isinstance(m, ast.Assign):
            for target in m.targets:
                if isinstance(target.ctx, ast.Store):
                    if isinstance(target, ast.Name):
                        auxnum = local_vars.setdefault(target.id, m.lineno)
                        if m.lineno < auxnum:
                            local_vars[target.id] = m.lineno
                    elif isinstance(target, ast.Attribute):
                        auxnum = local_vars.setdefault(target.attr, m.lineno)
                        if m.lineno < auxnum:
                            local_vars[target.attr] = m.lineno
    # get function header definition arguments and default values
    arguments = n.args
    dict_ = {'args': get_names_args(arguments.posonlyargs,
                                    arguments.args,
                                    arguments.kwonlyargs,
                                    arguments.vararg,
                                    arguments.kwarg),
             'defaults': get_defaults(arguments.defaults, arguments.kw_defaults),
             'local_vars': local_vars}
    return dict_

def ast_function_defs(codelines):
    tree = ast.parse("".join(codelines))
    # print(ast.dump(tree, indent=4))
    funct_defs = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            dict_ = get_funcdef_node_data(n)
            funct_defs[n.lineno] = dict_
        elif isinstance(n, ast.ClassDef):
            for m in n.body:
                if isinstance(m, ast.FunctionDef):
                    dict_ = get_funcdef_node_data(m)
                    funct_defs[m.lineno] = dict_
    return funct_defs


def check_func_var_args(dic_err, func_defs):
    for header_func_line in func_defs:
        func_dict = func_defs[header_func_line]
        if 'args' in func_dict.keys():
            for arg in func_dict['args']:
                if not is_snake_case(arg):
                    dic_err = add_error(dic_err, header_func_line-1, "S010", arg_name=arg)
        if 'local_vars' in func_dict.keys():
            for lv, ln in func_dict['local_vars'].items():
                if not is_snake_case(lv):
                    dic_err = add_error(dic_err, ln-1, "S011", var_name=lv)
        if 'defaults' in func_dict.keys():
            if "#mutable" in func_dict['defaults']:
                    dic_err = add_error(dic_err, header_func_line-1, "S012")
    return dic_err


def analyze_code(lst_code):
    """Returns a dictionary with keys=lines and sorted errors lists as values"""
    dic_errors = {}
    # classification of lines to solve stages 1-4
    line_type = classify_lines(lst_code)
    # added checks from stage 5: S010 to S012 from AST
    funct_defs = ast_function_defs(lst_code)
    dic_errors = check_func_var_args(dic_errors, funct_defs)

    for i, line in enumerate(lst_code):
        # S001
        if len(line) > 79:
            dic_errors = add_error(dic_errors, i, "S001")
        # S002
        if i in line_type["code_lines"]:
            spaces = re.match(" +", line)
            if spaces:
                if len(spaces[0]) % 4 != 0:
                    dic_errors = add_error(dic_errors, i, "S002")
        # S003
        if i not in line_type["semicolon_exceptions"]:
            if i in line_type["code_with_inline_comment"]:
                inline = get_inline_comment(line.strip())
                strip_code = line.replace("#" + inline, "").strip()
            else:
                strip_code = line.strip()
            if re.search(";$", strip_code) is not None:
                dic_errors = add_error(dic_errors, i, "S003")
        # S004
        if i in line_type["code_with_inline_comment"]:
            if re.search(r"^[^#]+[^ #]+ ?#", line.strip()) is not None:
                dic_errors = add_error(dic_errors, i, "S004")
        # S005
        if (i in line_type["comments"]) or (i in line_type["code_with_inline_comment"]):
            if i in line_type["code_with_inline_comment"]:
                comment = get_inline_comment(line.strip())
            else:
                comment = line.strip()
            if re.search(r"\btodo\b", comment.lower()) is not None:
                dic_errors = add_error(dic_errors, i, "S005")
        # S006
        if (i > 0) and (i in line_type["code_lines"]):
            n_blanklines = count_blank_lines(i, line_type)
            if n_blanklines > 2:
                dic_errors = add_error(dic_errors, i, "S006")
        # S007
        if i in line_type["code_lines"]:
            const_type, spaces_const, c_name = get_construction(line)
            if const_type:
                if spaces_const > 1:
                    dic_errors = add_error(dic_errors, i, "S007", const_name=const_type)
                if const_type == "class":
                    if not is_camel_case(c_name):
                        dic_errors = add_error(dic_errors, i, "S008", cl_name=c_name)
                elif const_type == "def":
                    if not is_snake_case(c_name):
                        dic_errors = add_error(dic_errors, i, "S009", fn_name=c_name)
    # sort dictionary by line and by error code
    dic_errors_sorted_elems = {key: dict(sorted(value.items(), key=operator.itemgetter(0)))
                                         for key, value in dic_errors.items()}
    dic_errors_sorted = dict(sorted(dic_errors_sorted_elems.items(), key=operator.itemgetter(0)))
    return dic_errors_sorted


if __name__ == "__main__":
    path_ = sys.argv[1]
    files = get_files(path_)
    analyzed_files = {}

    for file in files:
        analyzed_files[file] = analyze_code(read_file(file))

    for file, dic_errors_sorted in analyzed_files.items():
        filename = re.sub(re.escape(os.sep), "\\\\", file)
        print_errors(dic_errors_sorted, error_desc, filename)






