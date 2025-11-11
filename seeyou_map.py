import pymem
import pymem.process
import psutil
import ctypes
import sys


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1
            )
            sys.exit(0)
        except Exception as e:
            print(f" Не удалось запросить права: {e}")
            return False
    return True


def list_modules(pm):
    modules = []
    try:
        for module in pm.list_modules():
            modules.append(module)
            print(f"   - {module.name} (0x{module.lpBaseOfDll:X})")
    except:
        try:
            for module in pymem.process.list_modules(pm.process_handle):
                module_name = module.name.decode('utf-8', errors='ignore')
                modules.append(module_name)
                print(f"   - {module_name} (0x{module.lpBaseOfDll:X})")
        except:
            print(" Не удалось получить список модулей")
    return modules


def patch_fog_of_war(pm, base_address):
    fog_address = base_address + 0x740930

    try:
        original_bytes = pm.read_bytes(fog_address, 7)
        expected_bytes = b"\x8B\x81\x70\x09\x00\x00"

        if original_bytes[:6] == expected_bytes:
            fog_patch = b"\x33\xC0\x90\x90\x90\x90"
            pm.write_bytes(fog_address, fog_patch, len(fog_patch))
            current_bytes = pm.read_bytes(fog_address, 6)

            if current_bytes == fog_patch:
                print("ТУМАН УДАЛЕН!")
            else:
                print("Ошибка")
                return False
        else:
            print(f"Байты тумана не совпадают Ожидалось: {expected_bytes.hex()}")
            alt_patch = b"\x31\xC0"  # xor eax,eax
            pm.write_bytes(fog_address, alt_patch, 2)
            current_bytes = pm.read_bytes(fog_address, 2)
            if current_bytes == alt_patch:
                print("Альтернативный патч тумана применен!")
            else:
                print("Альтернативный патч тоже не сработал")
                return False

        return True

    except Exception as e:
        print(f"Ошибка патча тумана: {e}")
        return False


def change_memory_value():
    try:
        pm = pymem.Pymem("war3.exe")
        modules_list = list_modules(pm)

        target_module = None
        for mod_name in ["Game.dll", "war3.exe"]:
            try:
                if hasattr(pm, "list_modules"):
                    for module in pm.list_modules():
                        if mod_name.lower() in module.name.lower():
                            target_module = module
                            break
                else:
                    target_module = pymem.process.module_from_name(pm.process_handle, mod_name)

                if target_module:
                    print(f"Используем модуль: {mod_name}")
                    break
            except:
                continue

        if not target_module:
            if modules_list:
                target_module = modules_list[0]
                print(
                    f"Используем первый модуль: {target_module.name if hasattr(target_module, 'name') else target_module}")

        if hasattr(target_module, 'lpBaseOfDll'):
            base_address = target_module.lpBaseOfDll
        else:
            target_module = pymem.process.module_from_name(pm.process_handle, "war3.exe")
            base_address = target_module.lpBaseOfDll

        target_address = base_address + 0x3A1563

        original_bytes = pm.read_bytes(target_address, 4)
        print(f"Текущие байты видимости: {original_bytes.hex()}")

        new_bytes = b"\x66\xB9\x01\x00"
        print("Записываем новые байты видимости...")
        pm.write_bytes(target_address, new_bytes, len(new_bytes))

        current_bytes = pm.read_bytes(target_address, 4)
        print(f"Новые байты видимости: {current_bytes.hex()}")

        if current_bytes == new_bytes:
            print("Видимость юнитов изменена")
        else:
            print("Ошибка")

        fog_success = patch_fog_of_war(pm, base_address)

        if fog_success:
            print("\n" + "=" * 50)
            print("ВСЕ ПАТЧИ ПРИМЕНЕНЫ УСПЕШНО")
            print("Видимость юнитов: ВКЛЮЧЕНА")
            print("Туман войны: ОТКЛЮЧЕН")
            print("=" * 50)
        else:
            print("\nПатч видимости применен, но патч тумана не сработал")

    except Exception as e:
        print(f" Ошибка: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("🛠️  Warcraft III Memory Patcher")
    print("   📍 Видимость юнитов + Удаление тумана")
    print("=" * 50)

    if not run_as_admin():
        print("⚠️  Запуск без прав администратора!")
        print("⚠️  Возможны проблемы с доступом!")

    change_memory_value()
    input("\nНажми Enter для выхода...")
