import clingo
import constants
from tree_data import TreeData
from ast_visitor import ASTCopier
from predicate import Predicate, predicate_dependency
from variable_counter import VariableCounter
from aggregate_counter import AggregateCounter
from ast_wrappers.literal import Literal



def get_function_counting_literals(rule, counting_vars):
    """
        Gets and verifies counting literals of functions from the rule
        Returns counting_literals, if any
    """
    # Get potential counting functions i.e.:
    #  every Literal in body with child_keys ['atom'] and positive (none) sign
    #  child ['atom'] having type SymbolicAtom with child keys ['term']
    #  child ['term'] having type Function with child keys ['arguments']
    #   where ['arguments'] has one or more variables
    potential_literals = []
    # We are guaranteed to have a body if we have counting variables
    for body_literal in rule['body']:
        if body_literal.child_keys == ['atom'] and \
                body_literal.sign != clingo.ast.Sign.Negation and \
                body_literal.sign != clingo.ast.Sign.DoubleNegation:
            if body_literal['atom'].type == clingo.ast.ASTType.SymbolicAtom and \
                    body_literal['atom'].child_keys == ['term']:
                if body_literal['atom']['term'].type == clingo.ast.ASTType.Function and \
                        body_literal['atom']['term'].child_keys == ['arguments'] and \
                        len(body_literal['atom']['term']['arguments']) > 0:
                    potential_literals.append(body_literal)

    # Check exactly one counting variable appears in each potential function
    potential_literals_copy=potential_literals[:]
    for lit in potential_literals_copy:
        occurrences = 0
        for var in counting_vars:
            for lit_var in lit['atom']['term']['arguments']:
                # Comparing string representations avoids AttributeErrors
                if str(lit_var) == str(var):
                    occurrences = occurrences + 1
        if occurrences != 1:
            potential_literals.remove(lit)
    if len(potential_literals) < 1:
        return [],[]


    
    #n group deal with  :- u(X,Y), u(X,Y'), q(Y), q(Y'), Y < Y'.
    # group 1 u(X,Y),q(Y),
    # group 2 u(X,Y') ,q(Y')

    #  p_juq(X):-u(X,Y),q(Y)
    #  :-  {Y:u(X,Y),q(Y)}>2 ,p_juq(X).

    
    literal_groups=[[] for var_c in counting_vars]
    for grp_index,var_c in enumerate(counting_vars):
        for lit1 in potential_literals:
            for arg in lit1['atom']['term']['arguments']:
                if var_c == arg.name:
                    literal_groups[grp_index].append(lit1)
    

    length=len(literal_groups[0])
    for lg in literal_groups:
        if not length==len(lg):
            return [],[]
    
    literal_string_groups=[[] for var_c in literal_groups]
    strs=[]
    for index,lit_group in enumerate(literal_groups):
        for lit in lit_group:
            strs.append(str(lit))
        sorted(strs)
        str_liter=','.join(strs)
        for var_l in counting_vars:
            str_liter=str_liter.replace(var_l,counting_vars[0])
        literal_string_groups[index]=str_liter
        strs=[]

    

    for lit_str_indx1 in range(len(literal_string_groups)):
        for lit_str_indx2 in range(len(literal_string_groups)):
            if  lit_str_indx1!=  lit_str_indx2 :
                if  literal_string_groups[lit_str_indx1] != literal_string_groups[lit_str_indx2]:
                    return [],[]


    return potential_literals,literal_groups
    
    # Check that all potential functions are identical and have the same length
    for lit1 in potential_literals:
        func1 = str(lit1).split("(")[0]
        func1_arg_len = len(lit1['atom']['term']['arguments'])
        for lit2 in potential_literals:
            # This loop also compares each literal to itself and repeats
            #     comparisons, but this is trivial
            func2 = str(lit2).split("(")[0]
            func2_arg_len = len(lit2['atom']['term']['arguments'])
            if func1 != func2 or func1_arg_len != func2_arg_len:
                return []

    # Get the position of the counting variable in each of the potential
    #      counting literals
    position = -1
    lit_args = potential_literals[0]['atom']['term']['arguments']
    for var in counting_vars:
        if position != -1:
            break

        for i in range(len(lit_args)):
            if str(var) == str(lit_args[i]):
                position = i
                break

    # Then use that position to verify the location of the counting
    #    variable is the same for the for all the potential literals
    for lit in potential_literals:
        lit_var = lit['atom']['term']['arguments'][position]
        positional_occurrence = False
        for countVar in counting_vars:
            if str(lit_var) == str(countVar):
                positional_occurrence = True
        if not positional_occurrence:
            return []

    # Verify the non-counting variables are identical in all potential literals
    non_count_args = potential_literals[0]['atom']['term']['arguments'][:]
    non_count_args.remove(non_count_args[position])
    for otherLit in potential_literals:

        lit_args = otherLit['atom']['term']['arguments'][:]
        lit_args.remove(lit_args[position])

        if cmp(non_count_args, lit_args) != 0:  # returns 0 for equality
            return []

    return potential_literals


def get_function_counting_literals_eq(rule, counting_vars):
    """
        Gets and verifies counting literals of functions from the rule
        Returns counting_literals, if any
    """
    # Get potential counting functions i.e.:
    #  every Literal in body with child_keys ['atom'] and positive (none) sign
    #  child ['atom'] having type SymbolicAtom with child keys ['term']
    #  child ['term'] having type Function with child keys ['arguments']
    #   where ['arguments'] has one or more variables
    potential_literals = []
    # We are guaranteed to have a body if we have counting variables
    for body_literal in rule['body']:
        if body_literal.child_keys == ['atom'] and \
                body_literal.sign != clingo.ast.Sign.Negation and \
                body_literal.sign != clingo.ast.Sign.DoubleNegation:
            if body_literal['atom'].type == clingo.ast.ASTType.SymbolicAtom and \
                    body_literal['atom'].child_keys == ['term']:
                if body_literal['atom']['term'].type == clingo.ast.ASTType.Function and \
                        body_literal['atom']['term'].child_keys == ['arguments'] and \
                        len(body_literal['atom']['term']['arguments']) > 0:
                    for lit_var in body_literal['atom']['term']['arguments']:
                        if str(lit_var) in counting_vars:
                            potential_literals.append(body_literal)

    for body_literal in [rule['head']]:
        if body_literal.child_keys == ['atom'] and \
                body_literal.sign != clingo.ast.Sign.Negation and \
                body_literal.sign != clingo.ast.Sign.DoubleNegation:
            if body_literal['atom'].type == clingo.ast.ASTType.SymbolicAtom and \
                    body_literal['atom'].child_keys == ['term']:
                if body_literal['atom']['term'].type == clingo.ast.ASTType.Function and \
                        body_literal['atom']['term'].child_keys == ['arguments'] and \
                        len(body_literal['atom']['term']['arguments']) > 0:
                    for lit_var in body_literal['atom']['term']['arguments']:
                        if str(lit_var) in counting_vars:
                            potential_literals.append(body_literal)
    return potential_literals

def get_comparison_counting_literals(rule, counting_vars):
    """Gets and verifies counting literals of comparisons from the rule"""
    counting_literals = []

    for body_lit in rule['body']:

        # Literal must not be negated and must contain a comparison
        # There's no need to check 'not/'not not' for comparisons as clingo
        #     auto-rewrites this during parsing
        if body_lit.type == clingo.ast.ASTType.Literal and \
                body_lit.child_keys == ['atom'] and \
                body_lit['atom'].type == clingo.ast.ASTType.Comparison and \
                body_lit['atom']['comparison'] != clingo.ast.ComparisonOperator.Equal:

            # Left side of comparison must contain a counting variable
            left = None
            if str(body_lit['atom']['left']) in counting_vars:
                left = body_lit['atom']['left']

            # Handle cases where the left side of the comparison
            #    take one of the following forms:
            #         counting_variable {+,-} integer
            #        integer + counting_variable
            elif body_lit['atom']['left'].type == clingo.ast.ASTType.BinaryOperation:
                if str(body_lit['atom']['left']['left']) in counting_vars and \
                        body_lit['atom']['left']['right'].type == clingo.ast.ASTType.Symbol:
                    left = body_lit['atom']['left']['left']
                elif str(body_lit['atom']['left']['right']) in counting_vars and \
                        body_lit['atom']['left']['left'].type == clingo.ast.ASTType.Symbol and \
                        body_lit['atom']['left']['operator'] == clingo.ast.BinaryOperator.Plus:
                    left = body_lit['atom']['left']['right']

            # Right side of comparison must contain a counting variable
            right = None
            if str(body_lit['atom']['right']) in counting_vars:
                right = body_lit['atom']['right']

            # Right side may also take an alternative form
            elif body_lit['atom']['right'].type == clingo.ast.ASTType.BinaryOperation:
                if str(body_lit['atom']['right']['left']) in counting_vars and \
                        body_lit['atom']['right']['right'].type == clingo.ast.ASTType.Symbol:
                    right = body_lit['atom']['right']['left']
                elif str(body_lit['atom']['right']['right']) in counting_vars and \
                        body_lit['atom']['right']['left'].type == clingo.ast.ASTType.Symbol and \
                        body_lit['atom']['right']['operator'] == clingo.ast.BinaryOperator.Plus:
                    right = body_lit['atom']['right']['right']

            # If counting variables are found for both sides of the comparison,
            #     add it to the list of comparison counting literals
            if right is not None and left is not None:
                counting_literals.append(body_lit)

    return counting_literals



def find_min_var(counting_vars):
    min_var=counting_vars[0]
    min_length=1000
    for c_var in counting_vars:
        if len(c_var)<min_length:
            min_var=c_var
    return min_var


def get_comparison_counting_literals_eq(rule, counting_vars):
    """Gets and verifies counting literals of comparisons from the rule"""
    counting_literals = []

    for body_lit in rule['body']:

        # Literal must not be negated and must contain a comparison
        # There's no need to check 'not/'not not' for comparisons as clingo
        #     auto-rewrites this during parsing
        if body_lit.type == clingo.ast.ASTType.Literal and \
                body_lit.child_keys == ['atom'] and \
                body_lit['atom'].type == clingo.ast.ASTType.Comparison and \
                body_lit['atom']['comparison'] == clingo.ast.ComparisonOperator.Equal:

            # Left side of comparison must contain a counting variable
            left = None
            if str(body_lit['atom']['left']) in counting_vars:
                left = body_lit['atom']['left']

            # Handle cases where the left side of the comparison
            #    take one of the following forms:
            #         counting_variable {+,-} integer
            #        integer + counting_variable
            elif body_lit['atom']['left'].type == clingo.ast.ASTType.BinaryOperation:
                if str(body_lit['atom']['left']['left']) in counting_vars and \
                        body_lit['atom']['left']['right'].type == clingo.ast.ASTType.Symbol:
                    left = body_lit['atom']['left']['left']
                elif str(body_lit['atom']['left']['right']) in counting_vars and \
                        body_lit['atom']['left']['left'].type == clingo.ast.ASTType.Symbol and \
                        body_lit['atom']['left']['operator'] == clingo.ast.BinaryOperator.Plus:
                    left = body_lit['atom']['left']['right']

            # Right side of comparison must contain a counting variable
            right = None
            if str(body_lit['atom']['right']) in counting_vars:
                right = body_lit['atom']['right']

            # Right side may also take an alternative form
            elif body_lit['atom']['right'].type == clingo.ast.ASTType.BinaryOperation:
                if str(body_lit['atom']['right']['left']) in counting_vars and \
                        body_lit['atom']['right']['right'].type == clingo.ast.ASTType.Symbol:
                    right = body_lit['atom']['right']['left']
                elif str(body_lit['atom']['right']['right']) in counting_vars and \
                        body_lit['atom']['right']['left'].type == clingo.ast.ASTType.Symbol and \
                        body_lit['atom']['right']['operator'] == clingo.ast.BinaryOperator.Plus:
                    right = body_lit['atom']['right']['right']

            # If counting variables are found for both sides of the comparison,
            #     add it to the list of comparison counting literals
            if right is not None and left is not None:
                counting_literals.append(body_lit)

    for body_lit in [rule['head']]:

        # Literal must not be negated and must contain a comparison
        # There's no need to check 'not/'not not' for comparisons as clingo
        #     auto-rewrites this during parsing
        if body_lit.type == clingo.ast.ASTType.Literal and \
                body_lit.child_keys == ['atom'] and \
                body_lit['atom'].type == clingo.ast.ASTType.Comparison and \
                body_lit['atom']['comparison'] == clingo.ast.ComparisonOperator.Equal:

            # Left side of comparison must contain a counting variable
            left = None
            if str(body_lit['atom']['left']) in counting_vars:
                left = body_lit['atom']['left']

            # Handle cases where the left side of the comparison
            #    take one of the following forms:
            #         counting_variable {+,-} integer
            #        integer + counting_variable
            elif body_lit['atom']['left'].type == clingo.ast.ASTType.BinaryOperation:
                if str(body_lit['atom']['left']['left']) in counting_vars and \
                        body_lit['atom']['left']['right'].type == clingo.ast.ASTType.Symbol:
                    left = body_lit['atom']['left']['left']
                elif str(body_lit['atom']['left']['right']) in counting_vars and \
                        body_lit['atom']['left']['left'].type == clingo.ast.ASTType.Symbol and \
                        body_lit['atom']['left']['operator'] == clingo.ast.BinaryOperator.Plus:
                    left = body_lit['atom']['left']['right']

            # Right side of comparison must contain a counting variable
            right = None
            if str(body_lit['atom']['right']) in counting_vars:
                right = body_lit['atom']['right']

            # Right side may also take an alternative form
            elif body_lit['atom']['right'].type == clingo.ast.ASTType.BinaryOperation:
                if str(body_lit['atom']['right']['left']) in counting_vars and \
                        body_lit['atom']['right']['right'].type == clingo.ast.ASTType.Symbol:
                    right = body_lit['atom']['right']['left']
                elif str(body_lit['atom']['right']['right']) in counting_vars and \
                        body_lit['atom']['right']['left'].type == clingo.ast.ASTType.Symbol and \
                        body_lit['atom']['right']['operator'] == clingo.ast.BinaryOperator.Plus:
                    right = body_lit['atom']['right']['right']

            # If counting variables are found for both sides of the comparison,
            #     add it to the list of comparison counting literals
            if right is not None and left is not None:
                counting_literals.append(body_lit)

    return counting_literals


def get_counting_function_from_literals(counting_literals):
    """
        Given counting literals of functions and comparisons
        Returns first counting function encountered

        Will always find a counting function, as the counting
            literals are verified by other functions
    """
    for lit in counting_literals:
        if lit['atom'].type == clingo.ast.ASTType.SymbolicAtom and \
                lit['atom'].child_keys == ['term'] and \
                'name' in lit['atom']['term'].keys():
            return lit['atom']['term']

    print("Error: Cannot get counting function from counting literals")


def get_counting_function_args(counting_function, counting_vars):
    """
        Given a counting function and counting var
        Returns its arguments, the counting variable used in it,
            as well its set of arguments with the counting variable
            replaced by the anonymous variable

        Will always find a counting function, as the counting
            literals are verified by other functions
    """
    reg_args = counting_function['arguments'][:]
    anon_args = []
    ret_var = 'Error'
    for argVar in reg_args:
        if str(argVar) in counting_vars:
            anon_args.append(clingo.ast.Variable(constants.LOCATION, '_'))
            ret_var = argVar
        else:
            anon_args.append(argVar)

    return reg_args, ret_var, anon_args

def get_desired_input_output_form_pair_default(selection_dict,num):

    return selection_dict[num][0], selection_dict[num][1]

def get_desired_input_output_form_pair_fixed(selection_dict):

    return selection_dict[1][0], selection_dict[1][1]

def get_desired_input_output_form_pair(selection_dict):
    """
        Given a dictionary of  {id: (input form id, output form id)tuple}
        Prompts the user for a selection via the id key
        Returns the requested input form and output form ids
    """
    try:
        option = int(input("\nPlease select an input/output form pair by id  "))
    except ValueError:  # int(non-numeric) raises a ValueError
        option = -1
    while option not in selection_dict.keys():
        print ("Invalid id selected.")
        try:
            option = int(input("\nPlease select an input/output form pair by id  "))
        except ValueError:
            option = -1
    return selection_dict[option][0], selection_dict[option][1]


def print_valid_output_forms(valid_output_forms):
    """
        Prints to console all the available input/output form pairs, and
            an id next to each for selection
        Returns a dictionary of  {id: (input form id, output form id)tuple}
    """
    selection_dict = {}
    print ("\nValid Input/Output rewriting pairs:\n")
    print ("| ID |          Input Form          |         Output Form          |")

    selection_id = 1
    selection_id_padding = " "
    for input_form in valid_output_forms.keys():
        if len(valid_output_forms[input_form]) > 0:
            print ("")  # Skip line between different inputs
            for valid_output_form in valid_output_forms[input_form]:
                selection_dict[selection_id] = (input_form, valid_output_form)
                if selection_id >= 10:
                    selection_id_padding = ""

                print ("| %s%s | %s%s | %s%s |" % \
                      (selection_id_padding,
                       selection_id,
                       constants.FORM_TRANSLATION[input_form],
                       constants.FORM_TRANSLATION_PADDING[input_form],
                       constants.FORM_TRANSLATION[valid_output_form],
                       constants.FORM_TRANSLATION_PADDING[valid_output_form]))

                selection_id += 1
    return selection_dict

class EquivalenceTransformer:
    """
        This class is the basis for detecting and performing equivalence
        Every rule has its own EquivalenceTransformer
    """

    def __init__(self, rule, base_transformer):
        self.rule = rule
        self.base_transformer = base_transformer

        self.variable_counter = VariableCounter()
        self.variable_counter_eq = VariableCounter()
        self.aggregate_counter = AggregateCounter()
        self.valid_output_forms = {
            constants.NON_AGGR_FORM: [],
            constants.AGGR_FORM1: [],
            constants.AGGR_FORM2: [],
            constants.AGGR_FORM3: []
        }
        self.aux_rule = None
        self.aux_predicate = None
        self.rule_functions = []
        self.counting_literals = []
        self.counting_literals_groups=[]
        self.counting_variables = []
        self.counting_literals_eq = []
        self.ag_counting_function=None
        self.ag_guard_value=None

    def replace_equality_check(self, x, data=TreeData()):
        """
            Recursively traverse AST of the rule.
            Record encountered comparisons and functions for use in
                checking for potential rewritings of the rule
        """
        if isinstance(x, clingo.ast.AST):
            # Record non-equality comparisons for use in rewritability checking
            if x.type == clingo.ast.ASTType.Comparison:
                if x['comparison'] == clingo.ast.ComparisonOperator.Equal:
                    self.variable_counter_eq.mark_comparison_eq(x['left'], x['right'], x['comparison'])

            # Record body functions for use in rewritability checking
            #elif x.type == clingo.ast.ASTType.Function:
            #    if not data.head:
            #        self.rule_functions.append(x)

            return self.replace_eq_chk_children(x, data)

        elif isinstance(x, list):
            return [self.replace_equality_check(y, data) for y in x]
        elif x is None:
            return x
        else:
            raise TypeError("unexpected type")

    def replace_eq_chk_children(self, x, data=TreeData()):
        #if isinstance(x, list):
        #    return [self.replace_equality_check(y, data) for y in x]
        
        for key in x.child_keys:
            attr = self.replace_equality_check(x[key], TreeData(data.head or key == "head"))
            x[key] = attr
        return x



    def replace_all_eq_vars(self, node, counting_vars,replace_var):

        if isinstance(node, clingo.ast.AST):

            if node.type == clingo.ast.ASTType.Variable:
                if str(node) in counting_vars:
                    node.name=replace_var

            # If a node does not have arguments but has children, check children
            elif len(node.child_keys) > 0:
                for key in node.child_keys:
                    self.replace_all_eq_vars(node[key], counting_vars,replace_var)

        elif isinstance(node, list):

            for entry in node:
                self.replace_all_eq_vars(entry, counting_vars,replace_var)
        else:
            raise TypeError("unexpected type")

        
    def replace_eq_variables(self):
        """
         x1==x2,x2==x3  => x1
        """
        counting_vars = self.variable_counter_eq.get_counting_variables_eq()

        if len(counting_vars) > 1:

            check_rule = ASTCopier().deep_copy(self.rule)
            #get all eq predicates and literals.
            counting_literals = get_function_counting_literals_eq(check_rule, counting_vars)
            #get eq couting literals
            comparison_counting_literals_eq= get_comparison_counting_literals_eq(check_rule, counting_vars)

            if len(counting_literals) > 1:  # Must be at least two counting functions and one comparison
                
                self.counting_literals_eq = counting_literals + comparison_counting_literals_eq

                #the one (x1) to be replaced,  x1==x2,x2==x3  => x1
                chosen_variable=find_min_var(counting_vars)

                #remove x1==x2,x2==x3
                for lit in comparison_counting_literals_eq:
                    self.rule['body'].remove(lit)

                #replace all x1,x2,x3  => x1
                self.replace_all_eq_vars(self.rule,counting_vars,chosen_variable)

                '''
                if self.rule['head'] in counting_literals:
                    lit_cand=self.rule['head']
                    for arg_var in lit_cand['atom']['term'].arguments:
                        if arg_var in counting_vars:
                            arg_var.name=chosen_variable
                    
                    
                for lit_cand in self.rule['body']:
                    if lit_cand in counting_literals: 
                        for arg_var in lit_cand['atom']['term'].arguments:
                            if arg_var in counting_vars:
                                arg_var.name=chosen_variable
                '''

                

    def process_norm(self,valid_output_forms,rule_original):
        equiv_output_forms = self.rewritable_forms()  # Determines available output forms for this rule
        
        #self.base_transformer.Setting.VALID_AAGG=True
        
        if self.base_transformer.Setting.DEBUG:
            print ("equivalence_transformer: valid output forms:  " + str(equiv_output_forms))
        #print('process_norm')
        selection_dict = print_valid_output_forms(valid_output_forms)
        desired_input, desired_output = get_desired_input_output_form_pair_default(selection_dict,self.base_transformer.Setting.AGGR_FORM)

        #if self.base_transformer.Setting.AGGR_FORM in equiv_output_forms:
        if desired_output in equiv_output_forms:        
            self.rewrite_rule_norm(desired_output)
            self.print_rewrite(rule_original)
            self.confirm_rewrite_default(rule_original)  # Undoes rewriting if user denies rewrite
            self.base_transformer.Setting.VALID_AAGG=True
            
        elif len(equiv_output_forms) > 0:
            # Equivalent output forms exist, but not for the requested form.
            # Currently this only occurs for forms (2) and (3) because a cyclic dependency exists
            print ("Warning! Rule:  %s\n\nCould not be rewritten due to a cyclic dependency." % rule_original)

    def process_aagg(self,valid_output_forms,rule_original):
        if self.base_transformer.Setting.DEBUG:
            print ("equivalence_transformer: valid output forms:  " + str(
                valid_output_forms))
        #print(valid_output_forms.values())
        #print('process_aagg')
        self.base_transformer.Setting.VALID_AAGG=True
        

        sum_empty=sum([1 if i==[] else 0 for i in valid_output_forms.values()])
        if sum_empty != 4:  # Any rewriting possible

            # TODO: Perform all possible rewrites first and print rewritten
            #        rules to the console with id options
            #       Can handle multiple rewritings within a rule by performing
            #        every combination of rewriting, and giving each its own id
            selection_dict = print_valid_output_forms(valid_output_forms)
            desired_input, desired_output = get_desired_input_output_form_pair_default(selection_dict,self.base_transformer.Setting.AGGR_FORM)

            

            # TODO: implement rewrite_rule function to call a
            #        rewrite_rule_x_input(output_id) function for the given
            #        input, and perform projection as needed.
            self.rewrite_rule_aagg(desired_input, desired_output)
            self.print_rewrite(rule_original)
            self.confirm_rewrite_default(
                rule_original)  # Undoes rewriting if user denies rewrite

    def process(self):
        """
            Processes a rule to perform rewriting
        """
        #if self.base_transformer.Setting.DEBUG:
            #print "equivalence_transformer: processing rule:  %s" % self.rule
        print ("equivalence_transformer: processing rule:  %s" % self.rule)
        rule_original = ASTCopier().deep_copy(self.rule)  # For resetting rule if rewrite is denied by user

        #replace x1=x2,x2=x3,x3=x4,with x1
        self.rule=self.replace_equality_check(self.rule) #gather eq information
        self.replace_eq_variables()
        

        self.rule = self.explore(self.rule)  # Garners information for rewritability checking

        #        ex:    :- 2<=#count{X:F(X)}, 2<=#count{Z:G(Z)}.
        valid_output_forms = self.identify_output_forms(self.valid_output_forms)
   
        if valid_output_forms[constants.NON_AGGR_FORM]!=[]:
            self.process_norm(valid_output_forms,rule_original)
        elif valid_output_forms[constants.AGGR_FORM1]!=[] or valid_output_forms[constants.AGGR_FORM2]!=[] or valid_output_forms[constants.AGGR_FORM3]!=[]:
            self.process_aagg(valid_output_forms,rule_original)
        else:
            pass
    



    def explore(self, x, data=TreeData()):
        """
            Recursively traverse AST of the rule.
            Record encountered comparisons and functions for use in
                checking for potential rewritings of the rule
        """
        if isinstance(x, clingo.ast.AST):
            # Record non-equality comparisons for use in rewritability checking
            if x.type == clingo.ast.ASTType.Comparison:
                if x['comparison'] != clingo.ast.ComparisonOperator.Equal:
                    self.variable_counter.mark_comparison(x['left'], x['right'], x['comparison'])

            # Record body functions for use in rewritability checking
            elif x.type == clingo.ast.ASTType.Function:
                if not data.head:
                    self.rule_functions.append(x)

            # Record aggregate literals for use in rewritability checking
            elif x.type == clingo.ast.ASTType.Literal and \
                    x['atom'].type == clingo.ast.ASTType.BodyAggregate:
                self.aggregate_counter.record_aggregate_literal(x)

            return self.explore_children(x, data)

        elif isinstance(x, list):
            return [self.explore(y, data) for y in x]
        elif x is None:
            return x
        else:
            raise TypeError("unexpected type")

    def explore_children(self, x, data=TreeData()):
        for key in x.child_keys:
            attr = self.explore(x[key], TreeData(data.head or key == "head"))
            x[key] = attr
        return x

    def identify_output_forms(self, valid_output_forms):
        """
            Given empty dict of  {input_form_id: []}
            Identifies for each input form the valid output forms
            Returns populated dict of  {input_form_id: [valid_output_form_ids]}
        """
        valid_output_forms[constants.NON_AGGR_FORM] = self.identify_output_forms_non_aggregate_input()
        valid_output_forms[constants.AGGR_FORM1] = self.identify_output_forms_aggregate_form1_input()
        valid_output_forms[constants.AGGR_FORM2] = self.identify_output_forms_aggregate_form2_input()
        valid_output_forms[constants.AGGR_FORM3] = self.identify_output_forms_aggregate_form3_input()

        return valid_output_forms


    def identify_output_forms_non_aggregate_input(self):
        """
            Checks if the rule meets conditions to be rewritable by 
                aggregate equivalence for the given form.
            Forms (2) and (3) must satisfy the additional condition that 
                the counting predicate does not depend on the head predicates
            Returns the list of valid output forms for potential rewriting
        """
        counting_vars = self.variable_counter.get_counting_variables()
        if len(counting_vars) < 2:
            return []

        check_rule = ASTCopier().deep_copy(self.rule)

        counting_literals = get_function_counting_literals(check_rule,
                                                           counting_vars)[0]
        counting_literals += get_comparison_counting_literals(check_rule,
                                                              counting_vars)
        if len(counting_literals) < 3:
            # Must be at least two counting functions and one comparison
            return []

        if self.counting_vars_used_elsewhere(check_rule,
                                             counting_literals,
                                             counting_vars):
            return []

        counting_function = get_counting_function_from_literals(
            counting_literals)
        counting_predicate = Predicate(counting_function['name'],
                                       len(counting_function['arguments']))

        # record counting literal and variable information for performing rewriting later
        self.counting_literals = counting_literals
        self.counting_variables = counting_vars

        

        if self.circular_dependencies(counting_predicate):
            valid_forms = [constants.AGGR_FORM1]
        else:
            valid_forms = [constants.AGGR_FORM1,
                           constants.AGGR_FORM2,
                           constants.AGGR_FORM3]
        return valid_forms

    def identify_output_forms_aggregate_form1_input(self):
        """
            Identify whether rule is candidate for rewriting from the aggregate
                form 1 into any other form.
            Forms (2) and (3) must satisfy the additional condition that
                the counting predicate does not depend on the head predicates
            Returns list of IDs of valid output forms.

            TODO: Handle when |Y|>0
            TODO: Verification of rewriting for all sets of rewritable
                    aggregate literals within a rule, and recording of this
                    verification
        """
        aggregate_data = self.aggregate_counter.rewritable_aggregate_data[constants.AGGR_FORM1]
        if len(aggregate_data) == 0:
            return []  # no valid forms

        # TODO: Verification and recording of EACH possible aggregate literal
        aggregate_data_tuple = aggregate_data[0]

        counting_variable = aggregate_data_tuple[0]
        counting_function = aggregate_data_tuple[1]
        guard_value = aggregate_data_tuple[2]
        aggregate_literal = aggregate_data_tuple[3]

        if guard_value < 2:  # aggregate guard less than 2
            return []  # no valid forms

        check_rule = ASTCopier().deep_copy(self.rule)
        if self.counting_vars_used_elsewhere(check_rule,
                                             [aggregate_literal],
                                             [str(counting_variable)]):
            return []

        # record counting literal and variable information for performing rewriting later
        # TODO: New way of recording counting literals and variables
        self.counting_literals = [aggregate_literal]
        self.counting_variables = [str(counting_variable)]
        self.ag_counting_function=counting_function
        self.ag_guard_value=guard_value

        counting_predicate = Predicate(counting_function['name'],
                                       len(counting_function['arguments']))
        if self.circular_dependencies(counting_predicate):
            valid_forms = [constants.NON_AGGR_FORM]
        else:
            valid_forms = [constants.NON_AGGR_FORM,
                           constants.AGGR_FORM2,
                           constants.AGGR_FORM3]
        return valid_forms

    def identify_output_forms_aggregate_form2_input(self):
        """
            Identify whether rule is candidate for rewriting from the aggregate
                form 2 into any other form.
            Forms non-aggregate and inequality must satisfy the additional
                condition that the counting predicate does not depend on the
                head predicates
            Returns list of IDs of valid output forms.

            TODO: Handle when |Y|>0
            TODO: Verification of rewriting for all sets of rewritable
                    aggregate literals within a rule, and recording of this
                    verification
        """
        aggregate_data = self.aggregate_counter.rewritable_aggregate_data[constants.AGGR_FORM2]
        if len(aggregate_data) == 0:
            return []  # no valid forms

        # TODO: Verification and recording of EACH possible aggregate literal
        aggregate_data_tuple = aggregate_data[0]

        counting_variable = aggregate_data_tuple[0]
        counting_function = aggregate_data_tuple[1]
        guard_value = aggregate_data_tuple[2]
        aggregate_literal = aggregate_data_tuple[3]

        self.ag_counting_function=counting_function
        self.ag_guard_value=guard_value

        if guard_value < 2:  # aggregate guard less than 2
            return []  # no valid forms

        check_rule = ASTCopier().deep_copy(self.rule)
        # TODO: Fix this check. Not working in tests/testInequalityAggregateInput.lp
        if self.counting_vars_used_elsewhere(check_rule,
                                             [aggregate_literal],
                                             [str(counting_variable)]):
            return []

        # record counting literal and variable information for performing rewriting later
        # TODO: New way of recording counting literals and variables
        self.counting_literals = [aggregate_literal]
        self.counting_variables = [str(counting_variable)]

        counting_predicate = Predicate(counting_function['name'],
                                       len(counting_function['arguments']))
        if self.circular_dependencies(counting_predicate):
            valid_forms = [constants.AGGR_FORM3]
        else:
            valid_forms = [constants.NON_AGGR_FORM,
                           constants.AGGR_FORM1,
                           constants.AGGR_FORM3]
        return valid_forms

    def identify_output_forms_aggregate_form3_input(self):
        """
            Identify whether rule is candidate for rewriting from the aggregate
                form 3 into any other form.
            Forms non-aggregate and inequality must satisfy the additional
                condition that the counting predicate does not depend on the
                head predicates
            Returns list of IDs of valid output forms.

            TODO: Handle when |Y|>0
            TODO: Verification of rewriting for all sets of rewritable
                    aggregate literals within a rule, and recording of this
                    verification
        """
        aggregate_data = self.aggregate_counter.rewritable_aggregate_data[constants.AGGR_FORM3]
        if len(aggregate_data) == 0:
            return []  # no valid forms

        aggregate_literal_sets = {}
        # Format:  { aggregate_literal_elements :
        #            [[counting_variable, counting_function],
        #             {guard values: aggregate_literals}] }
        for aggregate_data_tuple in aggregate_data:
            counting_variable = aggregate_data_tuple[0]
            counting_function = aggregate_data_tuple[1]
            guard_value = aggregate_data_tuple[2]
            aggregate_literal = aggregate_data_tuple[3]

            self.ag_counting_function=counting_function
            self.ag_guard_value=guard_value

            # AST objects are not hashable for keys, so use their string
            #  representations instead. Use the elements because the only
            #  difference we want to find is in the guard values.
            aggregate_string_key = str(aggregate_literal['atom']['elements'])
            if aggregate_string_key not in aggregate_literal_sets.keys():
                aggregate_literal_sets[aggregate_string_key] = [
                    [counting_variable, counting_function],
                    {guard_value: aggregate_literal}]
            else:
                aggregate_literal_sets[aggregate_string_key][1][guard_value] = aggregate_literal

        # TODO: Verification and recording of EACH possible set of
        #  aggregate literals
        aggregate_literal_set = aggregate_literal_sets[aggregate_literal_sets.keys()[0]]
        counting_variable = aggregate_literal_set[0][0]
        counting_function = aggregate_literal_set[0][1]
        guard_values = aggregate_literal_set[1].keys()
        guard_values.sort()




        # find highest b value for the set
        max_guard_value = -1
        while list(range(max_guard_value + 2)) == guard_values[:max_guard_value+2]:
            max_guard_value += 1

        if max_guard_value < 1:
            return []  # no valid forms


        self.ag_counting_function=counting_function
        self.ag_guard_value=max_guard_value+1

        aggregate_literals = []
        for guard_value in guard_values[:max_guard_value+1]:
            aggregate_literals.append(aggregate_literal_set[1][guard_value])

        check_rule = ASTCopier().deep_copy(self.rule)
        if self.counting_vars_used_elsewhere(check_rule,
                                             aggregate_literals,
                                             [str(counting_variable)]):
            return []

        # record counting literal and variable information for performing rewriting later
        # TODO: New way of recording counting literals and variables
        self.counting_literals = aggregate_literals
        self.counting_variables = [str(counting_variable)]

        counting_predicate = Predicate(counting_function['name'],
                                       len(counting_function['arguments']))
        if self.circular_dependencies(counting_predicate):
            valid_forms = [constants.AGGR_FORM2]
        else:
            valid_forms = [constants.NON_AGGR_FORM,
                           constants.AGGR_FORM1,
                           constants.AGGR_FORM2
                           ]
        return valid_forms


    def print_rewrite(self, rule_before_rewriting):
        """
            Prints to console the rule before and after rewriting, and
                an auxiliary rule, if any
        """
        print ("\nBefore rewriting: %s" % rule_before_rewriting)
        print ("After rewriting:  %s\n" % self.rule)
        if self.aux_rule is not None:
            print ("\t(Adds Auxiliary Rule)  %s\n" % self.aux_rule)
            print ("Warning: This is not strongly equivalent for programs with " \
                  "rules or facts containing the predicate:  %s\n" % \
                  self.aux_predicate)

    def confirm_rewrite_default(self, rule_before_rewriting):
        print("Rule rewriting confirmed.\n")

    def confirm_rewrite(self, rule_before_rewriting):
        """
            Given the rule before rewrite is performed.
            If rewriting is not confirmed by cli, prompts the user to
                confirm the proposed rewrite and acts accordingly.
            Otherwise the rule is automatically confirmed.
        """
        if not self.base_transformer.Setting.CONFIRM_REWRITE:
            
            option = input("Confirm rewriting (y/n) ").lower()
            if option == "n" or option == "no":
                print("Rule rewriting denied.\n")
                self.aux_rule = None
                self.rule = rule_before_rewriting
                if len(self.base_transformer.new_predicates)!=0:
                    self.base_transformer.new_predicates.remove(self.aux_predicate)
            else:
                print("Rule rewriting confirmed.\n")

    def counting_vars_used_elsewhere(self, check_rule, counting_literals, counting_vars):
        """
            Recursive wrapper for counting_vars_not_used_elsewhere_helper.
            Checks if any of the given counting variable occurs within 
                the given rule, not including the counting_literals
            Returns true if an occurrence is found; false otherwise
        """
        for lit in counting_literals:
            check_rule['body'].remove(lit)

        return self.counting_vars_used_elsewhere_helper(check_rule, counting_vars)

    def counting_vars_used_elsewhere_helper(self, node, counting_vars):
        """
            Recursively check children of all nodes in AST for 'arguments'
                child key, then check 'arguments' for counting variables
            Returns False if no occurrence
        """
        if isinstance(node, clingo.ast.AST):

            if node.type == clingo.ast.ASTType.Variable:
                if str(node) in counting_vars:
                    return True

            # If a node does not have arguments but has children, check children
            elif len(node.child_keys) > 0:
                ret = False
                for key in node.child_keys:
                    ret = ret or self.counting_vars_used_elsewhere_helper(node[key], counting_vars)
                return ret

        elif isinstance(node, list):
            ret = False
            for entry in node:
                ret = ret or self.counting_vars_used_elsewhere_helper(entry, counting_vars)
            return ret
        
        elif node is None:
            return False

        else:
            print ("unexpected type of node: %s" % node)
            raise TypeError("unexpected type")

    def circular_dependencies(self, counting_predicate):
        """
            Certain output forms for a rewriting are equivalent only if the
                predicates in the body of the input rule are not dependent 
                on the predicates in the head of the rule.
                (i.e. the rule forms no circular dependencies)
            A predicate x 'depends' on another predicate y if x is defined in
                a rule in which y is in the body. Ex:
                        "x(A) :- y(A)."
                However, the dependency property is transitive across predicates.
            Given a predicate, the counting predicate.
            Returns True if the counting predicate depends on any
                predicate in the head of the rule
        """
        for head_predicate in self.get_head_predicates():
            if predicate_dependency(
                    self.base_transformer.predicate_adjacency_list,
                    counting_predicate,
                    head_predicate):
                return True

        return False

    def get_head_predicates(self):
        """
            Uses the ASTPredicateMapper to get the predicate map for the 
                current rule. (slightly overkill)
            From the predicate map, returns a list of the predicates in 
                the head of the current rule
        """
        # generate a new map from the current rule
        self.base_transformer.predicate_mapper.clear_map()
        self.base_transformer.predicate_mapper.map_rule_predicates(self.rule)
        predicate_map = self.base_transformer.predicate_mapper.predicate_map

        # head predicates will be the only predicates with dependencies
        return predicate_map.keys()

    

    def rewritable_forms(self):
        """
            Checks if the rule meets conditions to be rewritable by 
                aggregate equivalence for the given form.
            Forms (2) and (3) must satisfy the additional condition that 
                the counting predicate does not depend on the head predicates
            Returns the list of valid output forms for potential rewriting
        """
        counting_vars = self.variable_counter.get_counting_variables()
        if len(counting_vars) < 2:
            return []

        check_rule = ASTCopier().deep_copy(self.rule)

        counting_literals,literal_grps = get_function_counting_literals(check_rule, counting_vars)
        counting_literals += get_comparison_counting_literals(check_rule, counting_vars)
        if len(counting_literals) < 3:  # Must be at least two counting functions and one comparison
            return []

        if self.counting_vars_used_elsewhere(check_rule, counting_literals, counting_vars):
            return []

        counting_functions =[]
        for lit in [[i] for i in literal_grps[0]]:
            cfun=get_counting_function_from_literals(lit)
            counting_functions.append(cfun)
        valid_forms=[constants.AGGR_FORM1, constants.AGGR_FORM2, constants.AGGR_FORM3]
        for counting_function in counting_functions:
            counting_predicate = Predicate(counting_function['name'], len(counting_function['arguments']))
            if self.circular_dependencies(counting_predicate):
                valid_forms = [constants.AGGR_FORM1]
                break


        #args all [X,Y] or [Y]
        #cant [X,Y] [Z,Y]
        for cfg1 in range(len(counting_functions)):
            for cfg2 in range(len(counting_functions)):
                if cfg1>cfg2:
                    cf1=counting_functions[cfg1]['arguments']
                    cf2=counting_functions[cfg2]['arguments']
                    if len(cf1)>1 and len(cf2)>1 and cf1!=cf2:
                        return []


        # record counting literal and variable information for performing rewriting later
        self.counting_literals = counting_literals
        self.counting_literals_groups=literal_grps
        self.counting_variables = counting_vars
        return valid_forms

    def get_projection_predicate(self, counting_function, counting_var, arity):
        """
            Creates a predicate for a new function with a name 
                following the pattern:
                    COUNTINGFUNCTIONNAME_proj_COUNTINGVAR#
                where # is initially empty.
            If a collision occurs with other function names in the current
                operating file, then # is 1. If there is still a 
                collision, # is incremented until there is none
            Returns the new projection predicate
        """
        new_predicate = Predicate(counting_function['name'] + '_project_' + str(counting_var), arity)
        iteration = 1
        while new_predicate in self.base_transformer.in_predicates or \
                new_predicate in self.base_transformer.new_predicates:
            new_predicate.name = new_predicate.name + str(iteration)
            iteration += 1

        self.base_transformer.new_predicates.add(new_predicate)
        return new_predicate

    def make_auxiliary_definition(self, counting_functions):
        """
            Given the counting function
            Return a literal of the counting function with the counting 
                variable projected out, and a rule which defines the 
                auxiliary term
            When this is called, we are certain to have a counting
                variable within the given counting_function
        """

        # Get the functions arguments, less its counting variable
        projected_args=None
        counting_function=None
        for cf in counting_functions:
            args = cf['arguments'][:]
            if len(args)>1:
                projected_args = args
                counting_function=cf

        for counting_var in self.counting_variables:
            for function_var in projected_args:
                if counting_var == str(function_var):
                    projected_args.remove(function_var)
                    break

        projection_predicate = self.get_projection_predicate(counting_function, counting_var, len(projected_args))

        # Make Function and Literal with projected arguments and name
        aux_function = clingo.ast.Function(constants.LOCATION,
                                           projection_predicate.name,
                                           projected_args,
                                           False)
        aux_literal = clingo.ast.Literal(constants.LOCATION,
                                         clingo.ast.Sign.NoSign,
                                         clingo.ast.SymbolicAtom(aux_function))

        # Make rule defining the auxiliary function
        counting_literals=[]
        for cf in counting_functions:
            counting_literal = clingo.ast.Literal(constants.LOCATION,
                                              clingo.ast.Sign.NoSign,
                                              clingo.ast.SymbolicAtom(cf))
            counting_literals.append(counting_literal)                        
        aux_rule = clingo.ast.Rule(constants.LOCATION, aux_literal, counting_literals)

        return projection_predicate, aux_literal, aux_rule

    def rewrite_rule_norm(self,desired_output):
        """Performs aggregate rewriting on the given rule"""
        for lit in self.counting_literals:
            self.rule['body'].remove(lit)


        counting_functions =[]
        for lit in [[i] for i in self.counting_literals_groups[0]]:
            cfun=get_counting_function_from_literals(lit)
            counting_functions.append(cfun)
        #counting_function = get_counting_function_from_literals(self.counting_literals)
        rewritten_literals = self.create_aggregate_literals(counting_functions,desired_output)
        projection_needed=False
        for cf in counting_functions:
            if len(cf['arguments']) > 1:
                projection_needed=True
                break

        if projection_needed:  # Projection needed if function has multiple arguments
            aux_predicate, aux_lit, aux_rule = self.make_auxiliary_definition(counting_functions)
            self.aux_predicate = aux_predicate
            self.aux_rule = aux_rule

            rewritten_literals.append(aux_lit)

        self.rule['body'] += rewritten_literals

    def rewrite_rule_aagg(self,desired_input, desired_output):
        """Performs aggregate rewriting on the given input and output form"""
        for lit in self.counting_literals:
            self.rule['body'].remove(lit)

        counting_function = self.ag_counting_function
        
        guard_value = self.ag_guard_value

        rewritten_literals = self.rewrite_aggregate_literals(desired_input, desired_output)


        '''
        if len(counting_function[
                   'arguments']) > 1:  # Projection needed if function has multiple arguments
            aux_predicate, aux_lit, aux_rule = self.make_auxiliary_definition(
                counting_function)
            self.aux_predicate = aux_predicate
            self.aux_rule = aux_rule

            rewritten_literals.append(aux_lit)
        '''
        self.rule['body'] += rewritten_literals

    def rewrite_aggregate_literals(self,desired_input, desired_output):
        
        counting_function = self.ag_counting_function
        guard_value = self.ag_guard_value

        '''
        if desired_input==constants.AGGR_FORM1:
            guard_value = self.ag_guard_value
        '''
        ret=[]
        if desired_output==constants.NON_AGGR_FORM:
            allaaggvariables=[]
            args = counting_function['arguments'][:]
            counting_var=self.counting_variables[0]

            for guardid in range(1,guard_value+1):
                new_args=[]
                for arg in args:
                    if str(arg) == counting_var:
                        aaggvariable=clingo.ast.Variable(constants.LOCATION, str(arg)+'_AAGG_'+str(guardid))
                        allaaggvariables.append(aaggvariable)
                        new_args.append(aaggvariable)
                    else:
                        new_args.append(arg)

                aux_function = clingo.ast.Function(constants.LOCATION,
                                           counting_function.name,
                                           new_args,
                                           False)
                aux_literal = clingo.ast.Literal(constants.LOCATION,
                                         clingo.ast.Sign.NoSign,
                                         clingo.ast.SymbolicAtom(aux_function))
                
                ret.append(aux_literal)
            for i,v in enumerate (allaaggvariables[:-1]):
                leftv=allaaggvariables[i]
                rightv=allaaggvariables[i+1]
                cmpterm=clingo.ast.Comparison(clingo.ast.ComparisonOperator.LessThan,leftv,rightv)

                new_liter=clingo.ast.Literal(constants.LOCATION,
                                         clingo.ast.Sign.NoSign,
                                         cmpterm)
                ret.append(new_liter)
        if desired_output==constants.AGGR_FORM2:
            counting_var=self.counting_variables[0]
            rewritten_func=self.ag_counting_function
            rewritten_lit=clingo.ast.Literal(constants.LOCATION,
                                               clingo.ast.Sign.NoSign,
                                               clingo.ast.SymbolicAtom(rewritten_func))
            
            aggregate_components = [clingo.ast.BodyAggregateElement([counting_var], [rewritten_lit])]

            # Form:  not {} < b
            aggr_left_guard = None
            aggr_right_guard = clingo.ast.AggregateGuard(clingo.ast.ComparisonOperator.LessThan,
                                                         clingo.ast.Symbol(constants.LOCATION, guard_value))

            if self.base_transformer.Setting.USE_ANON:
                rwn_aggr = clingo.ast.Aggregate(constants.LOCATION,
                                                aggr_left_guard,
                                                aggregate_components,
                                                aggr_right_guard)
            else:
                rwn_aggr = clingo.ast.BodyAggregate(constants.LOCATION,
                                                    aggr_left_guard,
                                                    clingo.ast.AggregateFunction.Count,
                                                    aggregate_components,
                                                    aggr_right_guard)

            ret = [clingo.ast.Literal(constants.LOCATION, clingo.ast.Sign.Negation, rwn_aggr)]

        if desired_output==constants.AGGR_FORM1:
            counting_var=self.counting_variables[0]
            rewritten_func=self.ag_counting_function
            rewritten_lit=clingo.ast.Literal(constants.LOCATION,
                                               clingo.ast.Sign.NoSign,
                                               clingo.ast.SymbolicAtom(rewritten_func))
            
            aggregate_components = [clingo.ast.BodyAggregateElement([counting_var], [rewritten_lit])]

            # Form:  b <= {}
            aggr_left_guard =  clingo.ast.AggregateGuard(clingo.ast.ComparisonOperator.LessEqual,
                                                        clingo.ast.Symbol(constants.LOCATION, guard_value))
            aggr_right_guard = None


            if self.base_transformer.Setting.USE_ANON:
                rwn_aggr = clingo.ast.Aggregate(constants.LOCATION,
                                                aggr_left_guard,
                                                aggregate_components,
                                                aggr_right_guard)
            else:
                rwn_aggr = clingo.ast.BodyAggregate(constants.LOCATION,
                                                    aggr_left_guard,
                                                    clingo.ast.AggregateFunction.Count,
                                                    aggregate_components,
                                                    aggr_right_guard)

            ret = [clingo.ast.Literal(constants.LOCATION, clingo.ast.Sign.NoSign, rwn_aggr)]


        if desired_output==constants.AGGR_FORM3:

            counting_var=self.counting_variables[0]
            rewritten_func=self.ag_counting_function
            rewritten_lit=clingo.ast.Literal(constants.LOCATION,
                                               clingo.ast.Sign.NoSign,
                                               clingo.ast.SymbolicAtom(rewritten_func))
            
            aggregate_components = [clingo.ast.BodyAggregateElement([counting_var], [rewritten_lit])]

            ret = []
            for i in range(1, guard_value + 1):  # range 1..b

                aggr_left_guard = clingo.ast.AggregateGuard(clingo.ast.ComparisonOperator.Equal,
                                                            clingo.ast.Symbol(constants.LOCATION,
                                                                              guard_value - i))
                aggr_right_guard = None

                # Use specified aggregate inside form (see above)
                if self.base_transformer.Setting.USE_ANON:
                    rwn_aggr = clingo.ast.Aggregate(constants.LOCATION,
                                                    aggr_left_guard,
                                                    aggregate_components,
                                                    aggr_right_guard)
                else:
                    rwn_aggr = clingo.ast.BodyAggregate(constants.LOCATION,
                                                        aggr_left_guard,
                                                        clingo.ast.AggregateFunction.Count,
                                                        aggregate_components,
                                                        aggr_right_guard)

                aggr_literal = clingo.ast.Literal(constants.LOCATION, clingo.ast.Sign.Negation, rwn_aggr)
                ret.append(aggr_literal)

        return ret




    def create_aggregate_literals(self, counting_functions,desired_output):
        """
            Given a function.
            Creates counting aggregate literal(s) of the user
                specified form with the given counting function
                
            Returns aggregate literal(s) as a list
        """

        #desired_output=self.base_transformer.Setting.AGGR_FORM
        counting_function_grps=[]
        for counting_function in counting_functions:
            counting_function_grp=[]
            function_name = counting_function['name']
            counting_function_grp.append(function_name)
            regular_args, counting_var, anonymous_args = get_counting_function_args(counting_function,
                                                                                self.counting_variables)
            counting_function_grp.append(regular_args)
            counting_function_grp.append(counting_var)
            counting_function_grp.append(anonymous_args)
            counting_function_grps.append(counting_function_grp)
        
        '''
        #regular_args all [X,Y] or [Y]
        #cant [X,Y] [Z,Y]
        for cfg1 in range(len(counting_function_grps)):
            for cfg2 in range(len(counting_function_grps)):
                if cfg1>cfg2:
                    cf1=counting_function_grps[cfg1]
                    cf2=counting_function_grps[cfg2]
                    samearg= cf1[1]==cf2[1] or cf1[1]==[cf1[2]] or  cf2[1]==[cf2[2]]
                    if not samearg:
                        return None
        '''
        # Create aggregate elements having the form:
        #    "F(_,Y) : F(_,Y)"    if using anonymous variable, for proper grounding
        #    "X : F(X,Y)"         otherwise
        if self.base_transformer.Setting.USE_ANON:
            rewritten_literals=[]

            
            for counting_func in counting_function_grps:
                rewritten_function = clingo.ast.Function(constants.LOCATION, counting_func[0], counting_func[3], False)
                rewritten_literal = clingo.ast.Literal(constants.LOCATION,
                                                    clingo.ast.Sign.NoSign,
                                                    clingo.ast.SymbolicAtom(rewritten_function))
                rewritten_literals.append(rewritten_literal)
            
            aggregate_components = [clingo.ast.ConditionalLiteral(constants.LOCATION,
                                                                  rewritten_literals,
                                                                  rewritten_literals)]
            '''
                rewritten_function = clingo.ast.Function(constants.LOCATION, function_name, anonymous_args, False)
                rewritten_literal = clingo.ast.Literal(constants.LOCATION,
                                                    clingo.ast.Sign.NoSign,
                                                    clingo.ast.SymbolicAtom(rewritten_function))
            aggregate_components = [clingo.ast.ConditionalLiteral(constants.LOCATION,
                                                                  rewritten_literal,
                                                                  [rewritten_literal])]
            '''
        else:
            rewritten_literals=[]

            
            for counting_func in counting_function_grps:
                rewritten_function = clingo.ast.Function(constants.LOCATION, counting_func[0], counting_func[1], False)
                rewritten_literal = clingo.ast.Literal(constants.LOCATION,
                                                    clingo.ast.Sign.NoSign,
                                                    clingo.ast.SymbolicAtom(rewritten_function))
                rewritten_literals.append(rewritten_literal)
            
            aggregate_components = [clingo.ast.BodyAggregateElement([counting_function_grps[0][2]], rewritten_literals)]
            '''
            rewritten_function = clingo.ast.Function(constants.LOCATION, function_name, regular_args, False)
            rewritten_lit = clingo.ast.Literal(constants.LOCATION,
                                               clingo.ast.Sign.NoSign,
                                               clingo.ast.SymbolicAtom(rewritten_function))
            rewritten_function1 = clingo.ast.Function(constants.LOCATION, function_name, regular_args, False)
            rewritten_lit1 = clingo.ast.Literal(constants.LOCATION,
                                               clingo.ast.Sign.NoSign,
                                               clingo.ast.SymbolicAtom(rewritten_function1))
            aggregate_components = [clingo.ast.BodyAggregateElement([counting_var], [rewritten_lit,rewritten_lit1])]
            '''
        num_counting_vars = len(self.counting_variables)  # Let b be the number of counting variables

        # Make aggregate of one of three output forms, as specified by the user
        if desired_output == constants.AGGR_FORM3:
            # Form:  not b-1={}, not b-2={}, ..., not 0={}

            aggr_literals = []
            for i in range(1, num_counting_vars + 1):  # range 1..b

                aggr_left_guard = clingo.ast.AggregateGuard(clingo.ast.ComparisonOperator.Equal,
                                                            clingo.ast.Symbol(constants.LOCATION,
                                                                              num_counting_vars - i))
                aggr_right_guard = None

                # Use specified aggregate inside form (see above)
                if self.base_transformer.Setting.USE_ANON:
                    rwn_aggr = clingo.ast.Aggregate(constants.LOCATION,
                                                    aggr_left_guard,
                                                    aggregate_components,
                                                    aggr_right_guard)
                else:
                    rwn_aggr = clingo.ast.BodyAggregate(constants.LOCATION,
                                                        aggr_left_guard,
                                                        clingo.ast.AggregateFunction.Count,
                                                        aggregate_components,
                                                        aggr_right_guard)

                aggr_literal = clingo.ast.Literal(constants.LOCATION, clingo.ast.Sign.Negation, rwn_aggr)
                aggr_literals.append(aggr_literal)

        elif desired_output == constants.AGGR_FORM2:
            # Form:  not {} < b

            aggr_left_guard = None
            aggr_right_guard = clingo.ast.AggregateGuard(clingo.ast.ComparisonOperator.LessThan,
                                                         clingo.ast.Symbol(constants.LOCATION, num_counting_vars))

            if self.base_transformer.Setting.USE_ANON:
                rwn_aggr = clingo.ast.Aggregate(constants.LOCATION,
                                                aggr_left_guard,
                                                aggregate_components,
                                                aggr_right_guard)
            else:
                rwn_aggr = clingo.ast.BodyAggregate(constants.LOCATION,
                                                    aggr_left_guard,
                                                    clingo.ast.AggregateFunction.Count,
                                                    aggregate_components,
                                                    aggr_right_guard)

            aggr_literals = [clingo.ast.Literal(constants.LOCATION, clingo.ast.Sign.Negation, rwn_aggr)]

        else:
            # [Default case] Form:  b <= {}

            aggr_left_guard = clingo.ast.AggregateGuard(clingo.ast.ComparisonOperator.LessEqual,
                                                        clingo.ast.Symbol(constants.LOCATION, num_counting_vars))
            aggr_right_guard = None

            if self.base_transformer.Setting.USE_ANON:
                rwn_aggr = clingo.ast.Aggregate(constants.LOCATION,
                                                aggr_left_guard,
                                                aggregate_components,
                                                aggr_right_guard)
            else:
                rwn_aggr = clingo.ast.BodyAggregate(constants.LOCATION,
                                                    aggr_left_guard,
                                                    clingo.ast.AggregateFunction.Count,
                                                    aggregate_components,
                                                    aggr_right_guard)

            aggr_literals = [clingo.ast.Literal(constants.LOCATION, clingo.ast.Sign.NoSign, rwn_aggr)]

        return aggr_literals

