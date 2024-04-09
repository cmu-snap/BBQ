#!/usr/bin/python3
import math
from collections import deque
from typing import List, Tuple

class CodeGen:
    """Backend for generating SystemVerilog code."""
    def __init__(self) -> None:
        self.out = ""                       # Emitted code
        self.level = 0                      # Current indent level
        self.spacing = 4                    # Spacing per indent level
        self.stack = deque()                # Stack for tracking blocks


    @property
    def indent(self) -> int:
        """Fetch current indent spacing."""
        return self.level * self.spacing


    def tab(self, num: int=1) -> str:
        """Creates multi-tab indents."""
        return " " * self.spacing * num

    def inc_level(self) -> None:
        """Add indentation."""
        self.level += 1


    def dec_level(self) -> None:
        """Remove indentation."""
        assert self.level >= 0
        self.level -= 1


    def _format_str(self, x: str, offset: int) -> str:
        """Formats a string with the current indent."""
        assert isinstance(x, str) # Sanity check
        if not x: return x # Leave empty strings
        return (" " * (self.indent + offset)) + x


    def emit(self, x: str | List[str]="", indent_first: bool=True,
             offset: int=0, trailing_newline: bool=True) -> None:
        """Emit str (or list thereof) with the current indent."""
        if isinstance(x, str):
            if x: # Not an empty string
                self.out += (self._format_str(x, offset)
                             if indent_first else x)

        elif isinstance(x, list):
            first = True
            for v in x:
                if v is None: continue
                self.out += ((self._format_str(v, offset) if indent_first else v)
                             if first else "\n{}".format(self._format_str(v, offset)))

                first = False # First valid value

        # Sanity check
        else: assert False
        if trailing_newline: self.out += "\n"


    def comment(self, x: str | List[str], is_block: bool=False) -> None:
        """Emits a block or inline comment."""
        if is_block: self.emit("/**")

        prefix = " * " if is_block else "// "
        if isinstance(x, str):
            self.emit(prefix + x)
        else:
            assert isinstance(x, list)
            for v in x: self.emit(prefix + v)

        if is_block: self.emit(" */")


    def enum(self, name: str, values: List[str]) -> None:
        """Emit enum typedef with appropriate width."""

        # Sanity checks
        assert self.level == 0
        assert len(values) >= 2

        # Compute type width
        log_num_values = math.ceil(math.log2(len(values)))
        logictype = ("logic" if (log_num_values == 1) else
                     "logic [{}:0]".format(log_num_values - 1))

        self.emit("typedef enum {} {{".format(logictype))
        self.inc_level()

        for idx in range(len(values)):
            self.emit(values[idx], True, 0, False)
            if idx != (len(values) - 1): self.out += ","
            self.emit()

        self.dec_level()
        self.emit("}} {};".format(name))


    def align_assignment(self, lhs: str, rhs: str | List[str],
                         assign: str, tab_indent: bool=False) -> None:
        """Emit code of type: lhs = (rhs... (multi-line))."""
        assign_str = "{} {} ".format(lhs, assign)
        self.emit(assign_str, True, 0, False)

        # Account for additional brace/bracket
        offset = (self.spacing if tab_indent
                  else (len(assign_str) + 1))

        self.emit(rhs, False, offset, True)


    def align_defs(self, defs: List[Tuple], align : int=40) -> None:
        """Emit tab-aligned definitions."""
        for (lhs, rhs) in defs:
            if rhs is None: continue
            padding = align - len(lhs)
            assert padding > 0 # Sanity check
            self.emit(lhs + (" " * padding) + rhs)


    def _align_ternary_value(self, value: str | List[str],
                             value_pad: int) -> List[str]:
        """Helper method to format multi-line ternary values."""
        if isinstance(value, str): return [value]
        else:
            assert isinstance(value, list)
            if len(value) == 1: return value

        output_list = []
        for i, v in enumerate(value):
            output_list.append("({}".format(v) if (i == 0) else
                               "{}{}".format(" " * (value_pad + 1), v))
        output_list[-1] += ")"
        return output_list


    def align_ternary(
            self, lhs: str, conditionals: List[str],
            values: List[str | List[str]], assign: str,
            break_first: bool=True, same_line: bool=False) -> None:
        """Formats a ternary chain (a ? b : c ? ... : z) operation."""
        if same_line: assert len(conditionals) == 1
        if len(conditionals) > 1: assert break_first
        assert len(values) == (len(conditionals) + 1)

        output_list = []
        # Single ternary operator
        if len(conditionals) == 1:
            output = "{} {} (".format(lhs, assign)
            pad_same_line = self.spacing if break_first else len(output)

            if break_first:
                output_list.append(output)
                output = "{}{} ?".format(self.tab(), conditionals[0])

            else: output += "{} ?".format(conditionals[0])
            pad_staggered = len(output) + 1

            # Both values on the same line
            if same_line:
                output_list.append(output)
                assert isinstance(values[0], str)
                assert isinstance(values[1], str)
                output = "{}{} : {});".format(" " * pad_same_line,
                                              values[0], values[1])
                output_list.append(output)

            # Values on different lines
            else:
                value = self._align_ternary_value(
                    values[0], pad_staggered)

                value[0] = output + " " + value[0]
                value[-1] = value[-1] + " :"
                output_list.extend(value)

                value = self._align_ternary_value(
                    values[1], pad_staggered)

                value[0] = (" " * pad_staggered) + value[0]
                value[-1] = value[-1] + ");"
                output_list.extend(value)

        # Operator chain
        else:
            output_list.append("{} {} (".format(lhs, assign))
            pad_max = self.spacing + max([len(x) for x in conditionals])
            pad_rhs = pad_max + len(" ? ")

            for i, conditional in enumerate(conditionals):
                lhs_pad = pad_max - len(conditional)
                output = "{}{} ? ".format(" " * lhs_pad, conditional)

                value = self._align_ternary_value(values[i], pad_rhs)
                value[0] = output + value[0]
                value[-1] = value[-1] + " :"
                output_list.extend(value)

            # Last value
            value = self._align_ternary_value(values[-1], pad_rhs)
            value[0] = (" " * pad_rhs) + value[0]
            value[-1] = value[-1] + ");"
            output_list.extend(value)

        self.emit(output_list)


    def start_block(self, name: str) -> None:
        """Start a generic begin/end block."""
        self.emit("{} begin".format(name))
        self.stack.append(name)
        self.inc_level()


    def end_block(self, name: str) -> None:
        """End generic begin/end block."""
        self.dec_level()
        self.emit("end")
        assert self.stack.pop() == name


    def start_conditional(self, type: str, condition:
                          str | List[str]) -> None:
        """Start a conditional (if, else) block."""
        assert type in ["if", "else", "else if"]

        if type == "else":
            self.emit("else begin")
        else:
            self.emit("{} (".format(type), True, 0, False)
            self.emit(condition, False, len(type) + 2, False)
            self.emit(") begin", False, 0, True)

        self.stack.append(type)
        self.inc_level()


    def end_conditional(self, type: str) -> None:
        """Ends the current conditional block."""
        self.dec_level()
        self.emit("end")
        assert self.stack.pop() == type


    def start_for(self, var: str, condition: str) -> None:
        """Start a for block."""
        self.emit("for ({0} = 0; {1}; {0} = {0} + 1) begin"
                  .format(var, condition))

        self.stack.append("for")
        self.inc_level()


    def end_for(self) -> None:
        """Ends for block."""
        self.dec_level()
        self.emit("end")
        assert self.stack.pop() == "for"


    def start_switch(self, name: str) -> None:
        """Start a new switch/case block."""
        self.emit("case ({})".format(name))
        self.stack.append("switch")


    def end_switch(self) -> None:
        """End case block."""
        self.emit("endcase")
        assert self.stack.pop() == "switch"


    def start_case(self, casename: str) -> None:
        """Start a new switch/case statement."""
        self.emit("{}: begin".format(casename))
        self.stack.append("case")
        self.inc_level()


    def end_case(self) -> None:
        """End current case."""
        self.dec_level()
        self.emit("end")
        assert self.stack.pop() == "case"

    def start_ifdef(self, condition: str) -> None:
        """Start a new ifdef block."""
        self.emit("`ifdef {}".format(condition))
        self.stack.append("ifdef")


    def end_ifdef(self) -> None:
        """End current ifdef block."""
        self.emit("`endif")
        assert self.stack.pop() == "ifdef"
