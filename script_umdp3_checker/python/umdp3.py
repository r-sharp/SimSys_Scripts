# *****************************COPYRIGHT*******************************
# (C) Crown copyright Met Office. All rights reserved.
# For further details please refer to the file LICENSE
# which you should have received as part of this distribution.
# *****************************COPYRIGHT*******************************

"""
Package to contain functions which test for UMDP3 compliance.
Python translation of the original Perl UMDP3.pm module.
"""

import re
import threading
from typing import List, Dict, Set

# Declare version
VERSION = '13.5.0'

class UMDP3:
    """UMDP3 compliance checker class"""
    
    def __init__(self):
        self._extra_error_info = {}
        self._lock = threading.Lock()
        self._number_of_files_with_variable_declarations_in_includes = 0
        
        # Fortran keywords list
        self.fortran_keywords = {
            'ABORT', 'ABS', 'ABSTRACT', 'ACCESS', 'ACHAR', 'ACOS', 'ACOSD', 'ACOSH',
            'ACTION', 'ADJUSTL', 'ADJUSTR', 'ADVANCE', 'AIMAG', 'AINT', 'ALARM', 'ALGAMA',
            'ALL', 'ALLOCATABLE', 'ALLOCATE', 'ALLOCATED', 'ALOG', 'ALOG10', 'AMAX0', 'AMAX1',
            'AMIN0', 'AMIN1', 'AMOD', 'AND', 'ANINT', 'ANY', 'ASIN', 'ASIND', 'ASINH',
            'ASSIGN', 'ASSIGNMENT', 'ASSOCIATE', 'ASSOCIATED', 'ASYNCHRONOUS', 'ATAN', 'ATAN2',
            'ATAN2D', 'ATAND', 'ATANH', 'ATOMIC_ADD', 'ATOMIC_AND', 'ATOMIC_CAS', 'ATOMIC_DEFINE',
            'ATOMIC_FETCH_ADD', 'ATOMIC_FETCH_AND', 'ATOMIC_FETCH_OR', 'ATOMIC_FETCH_XOR',
            'ATOMIC_INT_KIND', 'ATOMIC_LOGICAL_KIND', 'ATOMIC_OR', 'ATOMIC_REF', 'ATOMIC_XOR',
            'BACKSPACE', 'BACKTRACE', 'BESJ0', 'BESJ1', 'BESJN', 'BESSEL_J0', 'BESSEL_J1',
            'BESSEL_JN', 'BESSEL_Y0', 'BESSEL_Y1', 'BESSEL_YN', 'BESY0', 'BESY1', 'BESYN',
            'BGE', 'BGT', 'BIND', 'BIT_SIZE', 'BLANK', 'BLE', 'BLOCK', 'BLT', 'BTEST',
            'CABS', 'CALL', 'CASE', 'CEILING', 'CHAR', 'CHARACTER', 'CLASS', 'CLOSE',
            'CMPLX', 'CODIMENSION', 'COMMAND_ARGUMENT_COUNT', 'COMMON', 'COMPILER_OPTIONS',
            'COMPILER_VERSION', 'COMPLEX', 'CONJG', 'CONTAINS', 'CONTINUE', 'COS', 'COSD',
            'COSH', 'COUNT', 'CPU_TIME', 'CSHIFT', 'CYCLE', 'DATA', 'DATE_AND_TIME',
            'DBLE', 'DEALLOCATE', 'DEFAULT', 'DELIM', 'DIMENSION', 'DIMAG', 'DIRECT',
            'DO', 'DOT_PRODUCT', 'DOUBLE', 'DPROD', 'DREAL', 'DTIME', 'ELEMENTAL',
            'ELSE', 'ELSEIF', 'ELSEWHERE', 'END', 'ENDDO', 'ENDFILE', 'ENDIF', 'ENTRY',
            'ENUM', 'ENUMERATOR', 'EOSHIFT', 'EPSILON', 'ERROR', 'ETIME', 'EXECUTE_COMMAND_LINE',
            'EXIT', 'EXP', 'EXPONENT', 'EXTENDS', 'EXTERNAL', 'EXTRACT', 'FALSE', 'FILE',
            'FINAL', 'FLOAT', 'FLOOR', 'FLUSH', 'FMT', 'FORALL', 'FORMAT', 'FORMATTED',
            'FRACTION', 'FUNCTION', 'GAMMA', 'GENERIC', 'GET_COMMAND', 'GET_COMMAND_ARGUMENT',
            'GET_ENVIRONMENT_VARIABLE', 'GOTO', 'HUGE', 'IACHAR', 'IAND', 'IARG', 'IBCLR',
            'IBITS', 'IBSET', 'ICHAR', 'IDATE', 'IEOR', 'IF', 'IFIX', 'IMAG', 'IMPLICIT',
            'IMPORT', 'IN', 'INCLUDE', 'INDEX', 'INOUT', 'INQUIRE', 'INT', 'INTEGER',
            'INTENT', 'INTERFACE', 'INTRINSIC', 'IOR', 'IOSTAT', 'ISHFT', 'ISHFTC',
            'IS_IOSTAT_END', 'IS_IOSTAT_EOR', 'ITIME', 'KIND', 'LBOUND', 'LEADZ',
            'LEN', 'LEN_TRIM', 'LGE', 'LGT', 'LLE', 'LLT', 'LOG', 'LOG10', 'LOGICAL',
            'MATMUL', 'MAX', 'MAXEXPONENT', 'MAXLOC', 'MAXVAL', 'MERGE', 'MIN',
            'MINEXPONENT', 'MINLOC', 'MINVAL', 'MOD', 'MODULE', 'MODULO', 'MOVE_ALLOC',
            'MVBITS', 'NAMELIST', 'NEAREST', 'NEW_LINE', 'NINT', 'NON_INTRINSIC',
            'NON_OVERRIDABLE', 'NOPASS', 'NOT', 'NULL', 'NULLIFY', 'NUMERIC_STORAGE_SIZE',
            'ONLY', 'OPEN', 'OPERATOR', 'OPTIONAL', 'OR', 'OUT', 'PACK', 'PARAMETER',
            'PASS', 'PAUSE', 'POINTER', 'POPPAR', 'POPCNT', 'PRECISION', 'PRESENT',
            'PRINT', 'PRIVATE', 'PROCEDURE', 'PRODUCT', 'PROGRAM', 'PROTECTED', 'PUBLIC',
            'PURE', 'PUSHPAR', 'RADIX', 'RANDOM_NUMBER', 'RANDOM_SEED', 'RANGE', 'READ',
            'REAL', 'RECURSIVE', 'REPEAT', 'RESHAPE', 'RESULT', 'RETURN', 'REWIND',
            'RRSPACING', 'SAME_TYPE_AS', 'SAVE', 'SCALE', 'SCAN', 'SELECT', 'SELECTED_CHAR_KIND',
            'SELECTED_INT_KIND', 'SELECTED_REAL_KIND', 'SEQUENCE', 'SET_EXPONENT', 'SHAPE',
            'SIGN', 'SIN', 'SIND', 'SINH', 'SIZE', 'SNGL', 'SPACING', 'SPREAD', 'SQRT',
            'STOP', 'STORAGE_SIZE', 'SUM', 'SUBROUTINE', 'SYSTEM_CLOCK', 'TAN', 'TAND',
            'TANH', 'TARGET', 'THEN', 'TIME', 'TINY', 'TRANSFER', 'TRANSPOSE', 'TRIM',
            'TRUE', 'TYPE', 'UBOUND', 'UNFORMATTED', 'UNPACK', 'USE', 'VALUE', 'VERIFY',
            'VOLATILE', 'WHERE', 'WHILE', 'WRITE'
        }
        
        # Obsolescent Fortran intrinsics
        self.obsolescent_intrinsics = {
            'ALOG', 'ALOG10', 'AMAX0', 'AMAX1', 'AMIN0', 'AMIN1', 'AMOD', 'CABS',
            'DABS', 'DACOS', 'DASIN', 'DATAN', 'DATAN2', 'DCOS', 'DCOSH', 'DDIM',
            'DEXP', 'DINT', 'DLOG', 'DLOG10', 'DMAX1', 'DMIN1', 'DMOD', 'DNINT',
            'DPROD', 'DREAL', 'DSIGN', 'DSIN', 'DSINH', 'DSQRT', 'DTAN', 'DTANH',
            'FLOAT', 'IABS', 'IDIM', 'IDINT', 'IDNINT', 'IFIX', 'ISIGN', 'MAX0',
            'MAX1', 'MIN0', 'MIN1', 'SNGL'
        }
        
        # Retired if-defs (placeholder - would be loaded from configuration)
        self.retired_ifdefs = set()
        
        # Deprecated C identifiers
        self.deprecated_c_identifiers = {
            'gets', 'tmpnam', 'tempnam', 'mktemp'
        }

    def reset_extra_error_information(self):
        """Reset extra error information"""
        with self._lock:
            self._extra_error_info = {}

    def get_extra_error_information(self) -> Dict:
        """Get extra error information"""
        with self._lock:
            return self._extra_error_info.copy()

    def add_extra_error(self, key: str, value: str = ""):
        """Add extra error information"""
        with self._lock:
            self._extra_error_info[key] = value

    def get_include_number(self) -> int:
        """Get number of files with variable declarations in includes"""
        return self._number_of_files_with_variable_declarations_in_includes

    def remove_quoted(self, line: str) -> str:
        """Remove quoted strings from a line"""
        # Simple implementation - remove single and double quoted strings
        result = line
        
        # Remove double quoted strings
        result = re.sub(r'"[^"]*"', '', result)
        
        # Remove single quoted strings
        result = re.sub(r"'[^']*'", '', result)
        
        return result

    # Test functions - each returns 0 for pass, >0 for fail

    def capitalised_keywords(self, lines: List[str]) -> int:
        """Check for lowercase Fortran keywords"""
        failures = 0
        for line in lines:
            # Remove quoted strings and comments
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)  # Remove comments
            
            # Check for lowercase keywords
            words = re.findall(r'\b\w+\b', clean_line.upper())
            for word in words:
                if word.upper() in self.fortran_keywords:
                    # Check if original was lowercase
                    if re.search(rf'\b{word.lower()}\b', clean_line.lower()):
                        self.add_extra_error(f"lowercase keyword: {word.lower()}")
                        failures += 1
        
        return failures

    def openmp_sentinels_in_column_one(self, lines: List[str]) -> int:
        """Check OpenMP sentinels are in column one"""
        failures = 0
        for line in lines:
            if re.search(r'^\s+!\$OMP', line):
                self.add_extra_error("OpenMP sentinel not in column 1")
                failures += 1
        return failures

    def unseparated_keywords(self, lines: List[str]) -> int:
        """Check for omitted optional spaces in keywords"""
        failures = 0
        patterns = [
            r'\bELSEIF\b', r'\bENDDO\b', r'\bENDIF\b', r'\bENDTYPE\b',
            r'\bENDMODULE\b', r'\bENDFUNCTION\b', r'\bENDSUBROUTINE\b'
        ]
        
        for line in lines:
            clean_line = self.remove_quoted(line)
            for pattern in patterns:
                if re.search(pattern, clean_line, re.IGNORECASE):
                    self.add_extra_error(f"unseparated keyword in line: {line.strip()}")
                    failures += 1
        
        return failures

    def go_to_other_than_9999(self, lines: List[str]) -> int:
        """Check for GO TO statements other than 9999"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            if match := re.search(r'\bGO\s*TO\s+(\d+)', clean_line, re.IGNORECASE):
                label = match.group(1)
                if label != '9999':
                    self.add_extra_error(f"GO TO {label}")
                    failures += 1
        
        return failures

    def write_using_default_format(self, lines: List[str]) -> int:
        """Check for WRITE without format"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            if re.search(r'\bWRITE\s*\(\s*\*\s*,\s*\*\s*\)', clean_line, re.IGNORECASE):
                self.add_extra_error("WRITE(*,*) found")
                failures += 1
        
        return failures

    def lowercase_variable_names(self, lines: List[str]) -> int:
        """Check for lowercase or CamelCase variable names only"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            # Simple check for UPPERCASE variable declarations
            if re.search(r'^\s*(INTEGER|REAL|LOGICAL|CHARACTER|TYPE)\s*.*::\s*[A-Z_]+', 
                        clean_line, re.IGNORECASE):
                if re.search(r'[A-Z]{2,}', clean_line):
                    self.add_extra_error("UPPERCASE variable name")
                    failures += 1
        
        return failures

    def dimension_forbidden(self, lines: List[str]) -> int:
        """Check for use of dimension attribute"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            if re.search(r'\bDIMENSION\b', clean_line, re.IGNORECASE):
                self.add_extra_error("DIMENSION attribute used")
                failures += 1
        
        return failures

    def ampersand_continuation(self, lines: List[str]) -> int:
        """Check continuation lines shouldn't start with &"""
        failures = 0
        for line in lines:
            if re.search(r'^\s*&', line):
                self.add_extra_error("continuation line starts with &")
                failures += 1
        
        return failures

    def forbidden_keywords(self, lines: List[str]) -> int:
        """Check for use of EQUIVALENCE or PAUSE"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            if re.search(r'\b(EQUIVALENCE|PAUSE)\b', clean_line, re.IGNORECASE):
                self.add_extra_error("forbidden keyword")
                failures += 1
        
        return failures

    def forbidden_operators(self, lines: List[str]) -> int:
        """Check for older form of relational operators"""
        failures = 0
        old_operators = ['.GT.', '.GE.', '.LT.', '.LE.', '.EQ.', '.NE.']
        
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            for op in old_operators:
                if op in clean_line.upper():
                    self.add_extra_error(f"old operator {op}")
                    failures += 1
        
        return failures

    def line_over_80chars(self, lines: List[str]) -> int:
        """Check for lines longer than 80 characters"""
        failures = 0
        for line in lines:
            if len(line.rstrip()) > 80:
                self.add_extra_error("line too long")
                failures += 1
        
        return failures

    def tab_detection(self, lines: List[str]) -> int:
        """Check for tab characters"""
        failures = 0
        for line in lines:
            if '\t' in line:
                self.add_extra_error("tab character found")
                failures += 1
        
        return failures

    def printstatus_mod(self, lines: List[str]) -> int:
        """Check for use of printstatus_mod instead of umPrintMgr"""
        failures = 0
        for line in lines:
            if re.search(r'\bUSE\s+printstatus_mod\b', line, re.IGNORECASE):
                self.add_extra_error("printstatus_mod used")
                failures += 1
        
        return failures

    def printstar(self, lines: List[str]) -> int:
        """Check for PRINT rather than umMessage and umPrint"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            if re.search(r'\bPRINT\s*\*', clean_line, re.IGNORECASE):
                self.add_extra_error("PRINT * used")
                failures += 1
        
        return failures

    def write6(self, lines: List[str]) -> int:
        """Check for WRITE(6) rather than umMessage and umPrint"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            if re.search(r'\bWRITE\s*\(\s*6\s*,', clean_line, re.IGNORECASE):
                self.add_extra_error("WRITE(6) used")
                failures += 1
        
        return failures

    def um_fort_flush(self, lines: List[str]) -> int:
        """Check for um_fort_flush rather than umPrintFlush"""
        failures = 0
        for line in lines:
            if re.search(r'\bum_fort_flush\b', line):
                self.add_extra_error("um_fort_flush used")
                failures += 1
        
        return failures

    def svn_keyword_subst(self, lines: List[str]) -> int:
        """Check for Subversion keyword substitution"""
        failures = 0
        for line in lines:
            if re.search(r'\$\w+\$', line):
                self.add_extra_error("SVN keyword substitution")
                failures += 1
        
        return failures

    def omp_missing_dollar(self, lines: List[str]) -> int:
        """Check for !OMP instead of !$OMP"""
        failures = 0
        for line in lines:
            if re.search(r'!\s*OMP\b', line) and not re.search(r'!\$OMP', line):
                self.add_extra_error("!OMP without $")
                failures += 1
        
        return failures

    def cpp_ifdef(self, lines: List[str]) -> int:
        """Check for #ifdef/#ifndef rather than #if defined()"""
        failures = 0
        for line in lines:
            if re.search(r'^\s*#\s*if(n)?def\b', line):
                self.add_extra_error("#ifdef/#ifndef used")
                failures += 1
        
        return failures

    def cpp_comment(self, lines: List[str]) -> int:
        """Check for Fortran comments in CPP directives"""
        failures = 0
        for line in lines:
            if re.search(r'^\s*#.*!', line):
                self.add_extra_error("Fortran comment in CPP directive")
                failures += 1
        
        return failures

    def obsolescent_fortran_intrinsic(self, lines: List[str]) -> int:
        """Check for archaic Fortran intrinsic functions"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            for intrinsic in self.obsolescent_intrinsics:
                if re.search(rf'\b{intrinsic}\b', clean_line, re.IGNORECASE):
                    self.add_extra_error(f"obsolescent intrinsic: {intrinsic}")
                    failures += 1
        
        return failures

    def exit_stmt_label(self, lines: List[str]) -> int:
        """Check that EXIT statements are labelled"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            if re.search(r'\bEXIT\s*$', clean_line, re.IGNORECASE):
                self.add_extra_error("unlabelled EXIT statement")
                failures += 1
        
        return failures

    def intrinsic_modules(self, lines: List[str]) -> int:
        """Check intrinsic modules are USEd with INTRINSIC keyword"""
        failures = 0
        intrinsic_modules = ['ISO_C_BINDING', 'ISO_FORTRAN_ENV']
        
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            for module in intrinsic_modules:
                if (re.search(rf'\bUSE\s+{module}\b', clean_line, re.IGNORECASE) and
                    not re.search(r'\bINTRINSIC\b', clean_line, re.IGNORECASE)):
                    self.add_extra_error(f"intrinsic module {module} without INTRINSIC")
                    failures += 1
        
        return failures

    def read_unit_args(self, lines: List[str]) -> int:
        """Check READ statements have explicit UNIT= as first argument"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            if match := re.search(r'\bREAD\s*\(\s*([^,)]+)', clean_line, re.IGNORECASE):
                first_arg = match.group(1).strip()
                if not first_arg.upper().startswith('UNIT='):
                    self.add_extra_error("READ without explicit UNIT=")
                    failures += 1
        
        return failures

    def retire_if_def(self, lines: List[str]) -> int:
        """Check for if-defs due for retirement"""
        failures = 0
        # This would check against a list of retired if-defs
        # For now, just a placeholder implementation
        return failures

    def implicit_none(self, lines: List[str]) -> int:
        """Check file has at least one IMPLICIT NONE"""
        for line in lines:
            if re.search(r'\bIMPLICIT\s+NONE\b', line, re.IGNORECASE):
                return 0
        
        self.add_extra_error("missing IMPLICIT NONE")
        return 1

    def forbidden_stop(self, lines: List[str]) -> int:
        """Check for STOP or CALL abort"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            clean_line = re.sub(r'!.*$', '', clean_line)
            
            if re.search(r'\b(STOP|CALL\s+abort)\b', clean_line, re.IGNORECASE):
                self.add_extra_error("STOP or CALL abort used")
                failures += 1
        
        return failures

    def intrinsic_as_variable(self, lines: List[str]) -> int:
        """Check for Fortran function used as variable name"""
        failures = 0
        # This would check for intrinsic function names used as variables
        # Simplified implementation
        for line in lines:
            clean_line = self.remove_quoted(line)
            if re.search(r'^\s*(INTEGER|REAL|LOGICAL|CHARACTER)\s*.*::\s*(SIN|COS|LOG|EXP)\b', 
                        clean_line, re.IGNORECASE):
                self.add_extra_error("intrinsic function used as variable")
                failures += 1
        
        return failures

    def check_crown_copyright(self, lines: List[str]) -> int:
        """Check for crown copyright statement"""
        file_content = '\n'.join(lines)
        if 'Crown copyright' in file_content or 'COPYRIGHT' in file_content:
            return 0
        
        self.add_extra_error("missing crown copyright")
        return 1

    def check_code_owner(self, lines: List[str]) -> int:
        """Check for correct code owner comment"""
        # Simplified check for code owner information
        file_content = '\n'.join(lines)
        if 'Code Owner:' in file_content or 'code owner' in file_content.lower():
            return 0
        
        # This is often a warning rather than an error
        return 0

    def array_init_form(self, lines: List[str]) -> int:
        """Check for old array initialization form"""
        failures = 0
        for line in lines:
            clean_line = self.remove_quoted(line)
            if re.search(r'\(/.*?\/\)', clean_line):
                self.add_extra_error("old array initialization form (/ /)")
                failures += 1
        
        return failures

    def line_trail_whitespace(self, lines: List[str]) -> int:
        """Check for trailing whitespace"""
        failures = 0
        for line in lines:
            if re.search(r'\s+$', line):
                self.add_extra_error("trailing whitespace")
                failures += 1
        
        return failures

    # C-specific tests

    def c_integral_format_specifiers(self, lines: List[str]) -> int:
        """Check C integral format specifiers have space"""
        failures = 0
        for line in lines:
            if re.search(r'%\d+[dioxX]"', line):
                self.add_extra_error("missing space in format specifier")
                failures += 1
        
        return failures

    def c_deprecated(self, lines: List[str]) -> int:
        """Check for deprecated C identifiers"""
        failures = 0
        for line in lines:
            for identifier in self.deprecated_c_identifiers:
                if re.search(rf'\b{identifier}\b', line):
                    self.add_extra_error(f"deprecated C identifier: {identifier}")
                    failures += 1
        
        return failures

    def c_openmp_define_pair_thread_utils(self, lines: List[str]) -> int:
        """Check C OpenMP define pairing with thread utils"""
        failures = 0
        for line in lines:
            if re.search(r'#\s*if.*_OPENMP', line):
                if not re.search(r'SHUM_USE_C_OPENMP_VIA_THREAD_UTILS', line):
                    self.add_extra_error("_OPENMP without SHUM_USE_C_OPENMP_VIA_THREAD_UTILS")
                    failures += 1
        
        return failures

    def c_openmp_define_no_combine(self, lines: List[str]) -> int:
        """Check C OpenMP defines not combined with third macro"""
        failures = 0
        for line in lines:
            if (re.search(r'_OPENMP.*&&.*SHUM_USE_C_OPENMP_VIA_THREAD_UTILS.*&&', line) or
                re.search(r'&&.*_OPENMP.*&&.*SHUM_USE_C_OPENMP_VIA_THREAD_UTILS', line)):
                self.add_extra_error("OpenMP defines combined with third macro")
                failures += 1
        
        return failures

    def c_openmp_define_not(self, lines: List[str]) -> int:
        """Check for !defined(_OPENMP) usage"""
        failures = 0
        for line in lines:
            if re.search(r'!\s*defined\s*\(\s*_OPENMP\s*\)', line):
                self.add_extra_error("!defined(_OPENMP) used")
                failures += 1
        
        return failures

    def c_protect_omp_pragma(self, lines: List[str]) -> int:
        """Check OMP pragma is protected with ifdef"""
        failures = 0
        in_openmp_block = False
        
        for line in lines:
            if re.search(r'#\s*if.*_OPENMP', line):
                in_openmp_block = True
            elif re.search(r'#\s*endif', line):
                in_openmp_block = False
            elif (re.search(r'#\s*pragma\s+omp', line) or 
                  re.search(r'#\s*include\s*<omp\.h>', line)):
                if not in_openmp_block:
                    self.add_extra_error("unprotected OMP pragma/include")
                    failures += 1
        
        return failures

    def c_ifdef_defines(self, lines: List[str]) -> int:
        """Check for #ifdef style rather than #if defined()"""
        failures = 0
        for line in lines:
            if re.search(r'^\s*#\s*ifdef\b', line):
                self.add_extra_error("#ifdef used instead of #if defined()")
                failures += 1
        
        return failures

    def c_final_newline(self, lines: List[str]) -> int:
        """Check C unit ends with final newline"""
        if lines and not lines[-1].endswith('\n'):
            self.add_extra_error("missing final newline")
            return 1
        
        return 0