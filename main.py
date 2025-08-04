import os
import subprocess
import sys
import re
import time
import logging
from datetime import datetime

if sys.version_info.major < 3:
    print("Error! requiere Python 3, Ejecute con python3")
    sys.exit(1)

try:
    logging.basicConfig(
        filename="logs.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
except PermissionError:
    print("Error: No se puede escribir en logs.log. Verifique permisos.")
    sys.exit(1)

def print_menu(commands):
    PURPLE = "\033[95m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    RESET = "\033[0m"
    try:
        print(f"""
{CYAN}
⠀⠀⠀⠀⠀⢀⡴⠋⠉⠛⠒⣄⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢸⠏⠀⠀⣶⡄⠀⠀⣛⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣿⠃⠀⠀⠀⠀⡤⠋⠠⠉⠡⢤⢀⠀
⠀⠀⠀⠀⢿⠀⠀⠀⠀⠀⢉⣝⠲⠤⣄⣀⣀⠌
⠀⠀⠀⠀⡏⠀⠀⠀⠀⠀⢸⠁⠀⠀⠀⠀⠀⠀
⠀⠀⠀⡴⠃⠀⠀⠀⠀⠀⠸⡄⠀⠀⠀⠀⠀⠀
⢀⠖⠋⠀⠀⠀⠀⠀⠀⠀⠀⠘⣆⠀⠀⠀⠀⠀
⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢳⠀⠀⠀⠀
{RESET}
{GREEN}Propiedad Greed's && Styx{RESET}
{CYAN}Comandos disponibles:{RESET}
        """)
        all_commands = []
        for cmds in commands.values():
            for cmd_name, _, description in cmds:
                all_commands.append((cmd_name, description))
        if not all_commands:
            print(f"{RED}No se encontraron comandos en el directorio plugins/{RESET}")
        for cmd_name, description in sorted(all_commands):
            print(f"{GREEN}- {cmd_name}{RESET}: {description}")
        print(f"\n{CYAN}Opciones:{RESET}")
        print(f"{GREEN}- menu{RESET}: Mostrar este menú")
        print(f"{GREEN}- cls{RESET}: Limpiar pantalla")
        print(f"{GREEN}- create{RESET}: Crear nuevo comando (-js, -py, -c, -sh)")
        print(f"{GREEN}- reload{RESET}: Recargar comandos")
        print(f"{GREEN}- owner{RESET}: Info del creador")
        print(f"{GREEN}- help{RESET}: Mostrar descripción de un comando")
        print(f"{GREEN}- exit{RESET}: Salir")
    except Exception as e:
        print(f"{RED}Error mostrando menú: {e}{RESET}")
        logging.error(f"Error en print_menu: {e}")

def load_commands():
    commands = {}
    try:
        for category in ["js", "py", "c", "sh"]:
            path = f"plugins/{category}"
            os.makedirs(path, exist_ok=True)
            commands[category] = []
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith(f".{category}"):
                        cmd_name = re.sub(f"\\.{category}$", "", file)
                        description = "Sin descripción"
                        file_path = os.path.join(path, file)
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                first_line = f.readline().strip()
                                if first_line.lower().startswith("# desc:"):
                                    description = first_line[7:].strip()
                        except Exception as e:
                            logging.warning(f"Error leyendo descripción de {file_path}: {e}")
                        commands[category].append((cmd_name, file, description))
        return commands
    except Exception as e:
        print(f"{RED}Error cargando comandos: {e}{RESET}")
        logging.error(f"Error en load_commands: {e}")
        return commands

def check_tool(tool):
    try:
        subprocess.run([tool, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def execute_command(cmd, commands, args):
    RED = "\033[31m"
    RESET = "\033[0m"
    try:
        for category, cmds in commands.items():
            for cmd_name, fname, _ in cmds:
                if cmd == cmd_name:
                    file_path = f"plugins/{category}/{fname}"
                    if not os.path.exists(file_path):
                        print(f"{RED}Error: Archivo {file_path} no encontrado{RESET}")
                        return True
                    if not os.access(file_path, os.X_OK) and category != "c":
                        try:
                            os.chmod(file_path, 0o755)
                        except PermissionError:
                            print(f"{RED}Error: No se pueden modificar permisos de {file_path}{RESET}")
                            return True
                    if category == "c":
                        executable = f"plugins/c/{cmd_name}"
                        source_file = file_path
                        if not os.path.exists(executable) or (os.path.getmtime(source_file) > os.path.getmtime(executable)):
                            print(f"Compilando {cmd_name}...")
                            try:
                                subprocess.run(["gcc", source_file, "-o", executable], check=True)
                                print(f"Compilado {cmd_name} exitosamente")
                            except subprocess.CalledProcessError:
                                print(f"{RED}Error compilando {cmd_name}{RESET}")
                                return True
                        if not os.path.exists(executable):
                            print(f"{RED}Ejecutable {executable} no encontrado{RESET}")
                            return True
                        cmd_to_run = [executable] + args
                    else:
                        interpreters = {
                            "js": "node",
                            "py": "python",
                            "sh": "bash"
                        }
                        interpreter = interpreters.get(category)
                        if not check_tool(interpreter):
                            print(f"{RED}Error: {interpreter} no está instalado{RESET}")
                            return True
                        cmd_to_run = [interpreter, file_path] + args
                    print(f"Ejecutando: {' '.join([cmd] + args)}")
                    subprocess.run(cmd_to_run, check=True)
                    logging.info(f"Ejecutado: {cmd} {' '.join(args)}")
                    return True
        return False
    except subprocess.CalledProcessError as e:
        print(f"{RED}Error ejecutando {cmd}: {e}{RESET}")
        logging.error(f"Error ejecutando {cmd}: {e}")
        return True
    except Exception as e:
        print(f"{RED}Error inesperado ejecutando {cmd}: {e}{RESET}")
        logging.error(f"Error inesperado ejecutando {cmd}: {e}")
        return True

def create_command(args):
    RED = "\033[31m"
    GREEN = "\033[32m"
    RESET = "\033[0m"
    try:
        if len(args) != 2 or args[0] not in ["-js", "-py", "-c", "-sh"]:
            print(f"{RED}Uso: create [-js|-py|-c|-sh] nombre_comando{RESET}")
            return
        category, cmd_name = args[0][1:], args[1]
        if not re.match(r"^[a-zA-Z0-9_-]+$", cmd_name):
            print(f"{RED}Error: El nombre del comando solo puede contener letras, números, guiones y guiones bajos{RESET}")
            return
        filename = f"{cmd_name}.{category}"
        path = f"plugins/{category}/{filename}"
        os.makedirs(f"plugins/{category}", exist_ok=True)
        
        template = f"# DESC: Nuevo comando {cmd_name}\n"
        if category == "js":
            template += "console.log('Comando en JavaScript');\n"
        elif category == "py":
            template += "print('Comando en Python')\n"
        elif category == "c":
            template += "#include <stdio.h>\nint main() {\n    printf(\"Comando en C\\n\");\n    return 0;\n}\n"
        elif category == "sh":
            template += "#!/bin/bash\necho 'Comando en Bash'\n"
        
        with open(path, "w") as f:
            f.write(template)
        subprocess.run(["nano", path])
        
        if category == "c":
            try:
                subprocess.run(["gcc", path, "-o", f"plugins/c/{cmd_name}"], check=True)
                print(f"{GREEN}Compilado {cmd_name} exitosamente{RESET}")
            except subprocess.CalledProcessError:
                print(f"{RED}Error compilando {cmd_name}{RESET}")
        logging.info(f"Creado comando: {cmd_name} ({category})")
    except Exception as e:
        print(f"{RED}Error creando comando: {e}{RESET}")
        logging.error(f"Error en create_command: {e}")

def get_command_description(cmd, commands):
    try:
        for category, cmds in commands.items():
            for cmd_name, _, description in cmds:
                if cmd == cmd_name:
                    return description
        return None
    except Exception as e:
        logging.error(f"Error en get_command_description: {e}")
        return None

def main():
    RED = "\033[31m"
    RESET = "\033[0m"
    try:
        commands = load_commands()
        while True:
            print_menu(commands)
            choice = input("\n> ").strip().split()
            if not choice:
                continue
            cmd, args = choice[0], choice[1:]

            if cmd == "exit":
                print("Saliendo de Greed's Suite...")
                break
            elif cmd == "menu":
                continue
            elif cmd == "cls":
                os.system("clear" if os.name != "nt" else "cls")
            elif cmd == "create":
                create_command(args)
            elif cmd == "reload":
                commands = load_commands()
                print(f"Comandos recargados")
            elif cmd == "owner":
                print(f"Creador: Styx")
            elif cmd == "help":
                if not args:
                    print(f"{RED}Uso: help <comando>{RESET}")
                else:
                    description = get_command_description(args[0], commands)
                    if description:
                        print(f"{args[0]}: {description}")
                    else:
                        print(f"{RED}Comando {args[0]} no encontrado{RESET}")
            else:
                if not execute_command(cmd, commands, args):
                    print(f"{RED}Comando no encontrado: {cmd}{RESET}")
    except KeyboardInterrupt:
        print("\nSaliendo de Greed's Suite...")
    except Exception as e:
        print(f"{RED}Error crítico en el programa: {e}{RESET}")
        logging.error(f"Error crítico en main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()