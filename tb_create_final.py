import re
import random

def read_and_analyze_verilog(file_path):
    with open(file_path, 'r') as file:
        verilog_code = file.read()

    parameters = {m.group(1): int(m.group(2)) for m in re.finditer(r'parameter\s+(\w+)\s*=\s*(\d+)', verilog_code)}
    module_name_search = re.search(r'module\s+(\w+)', verilog_code)
    module_name = module_name_search.group(1) if module_name_search else None
    ports_regex = re.compile(r'(input|output)\s+(reg|wire)?\s*\[?(\w+)?-?1?:?0?\]?\s*(\w+)', re.MULTILINE)
    ports = ports_regex.findall(verilog_code)

    input_output_info = []
    for direction, _, bit_range, name in ports:
        bit_size = 1  
        if bit_range in parameters:
            bit_size = parameters[bit_range] 
        elif bit_range.isdigit():
            bit_size = int(bit_range) + 1 
        input_output_info.append((name, bit_size, direction))

    return module_name, parameters, input_output_info

def generate_random_value(bit_size):
    max_value = 2**bit_size - 1
    random_value = random.randint(0, max_value)
    return f"{bit_size}'b{random_value:0{bit_size}b}"

def create_testbench(module_name, parameters, input_output_info, clk_period=2):
    clk_exists = any(name == "clk" for name, _, direction in input_output_info if direction == "input")
    tb_lines = [f"module tb_{module_name}();\n"]

    for param, value in parameters.items():
        tb_lines.append(f"parameter {param} = {value};\n")
    tb_lines.append("\n")

    tb_lines.append(f"parameter CLK_PERIOD = {clk_period};\n\n")

    tb_lines.append(f"{module_name} {module_name}0(\n")
    for i, (name, bits, _) in enumerate(input_output_info, start=1):
        connector = '' if i == len(input_output_info) else ','
        tb_lines.append(f".{name}({name}){connector}\n")
    tb_lines.append(");\n\n")

    for name, bits, direction in input_output_info:
        port_type = "reg" if direction == 'input' else "wire"
        bit_declare = f"[{bits-1}:0] " if bits > 1 else ""
        tb_lines.append(f"{port_type} {bit_declare}{name};\n")

    if clk_exists:
        tb_lines.append("\ninitial begin\n")
        tb_lines.append("clk = 0;\n")
        tb_lines.append("forever #(CLK_PERIOD/2) clk = ~clk;\n")
        tb_lines.append("end\n\n")

    tb_lines.append("initial begin\n")
    reset_exists = "rst" in [name for name, _, _ in input_output_info]
    if reset_exists:
        tb_lines.append("rst = 1;\n")
    for name, bits, direction in input_output_info:
        if direction == 'input' and name != "clk" and name != "rst":
            tb_lines.append(f"{name} = 0;\n")

    if reset_exists:
        tb_lines.append("\n#10 rst = 0;\n#10 rst = 1;\n")

    for _ in range(10):  # 변경 횟수 설정. 초기값 : 10
        for name, bits, direction in input_output_info:
            if direction == 'input' and name != "clk" and name != "rst":
                random_value = generate_random_value(bits)
                tb_lines.append(f"#10 {name} = {random_value};\n")

    tb_lines.append("#10 $finish();\n")
    tb_lines.append("end\n")
    tb_lines.append("endmodule\n")

    return tb_lines

file_path = 'path/to/your/verilog_file.v' # Source Code 경로 설정
module_name, parameters, input_output_info = read_and_analyze_verilog(file_path)

write_path = 'desired/path/to/tb_{module_name}.v'.format(module_name=module_name)  # 저장 경로 설정
testbench_lines = create_testbench(module_name, parameters, input_output_info)

# 테스트벤치 파일 저장
with open(write_path, "w") as f:
    f.writelines(testbench_lines)

print(f"Testbench written to {write_path}")
