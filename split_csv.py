"""Divide archivos CSV grandes en partes mas pequenas, repitiendo el encabezado en cada parte.

Uso:
    python split_csv.py archivo1.csv archivo2.csv ... [--max-mb 18] [--out-dir csv_partes]
"""
import argparse
import csv
import io
import os


def split_csv_parts(path: str, parts: int, out_dir: str) -> None:
    if parts < 1:
        raise ValueError("El numero de partes debe ser mayor que cero.")

    base_name = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(out_dir, exist_ok=True)

    with open(path, "r", newline="", encoding="utf-8-sig") as source:
        reader = csv.reader(source)
        header = next(reader)
        rows = list(reader)

    total_rows = len(rows)
    base_rows, extra_rows = divmod(total_rows, parts)
    start = 0

    for part_num in range(1, parts + 1):
        row_count = base_rows + (1 if part_num <= extra_rows else 0)
        part_path = os.path.join(out_dir, f"{base_name}_parte{part_num}.csv")
        with open(part_path, "w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output, lineterminator="\r\n")
            writer.writerow(header)
            writer.writerows(rows[start : start + row_count])
        print(f"Creando {part_path}: {row_count} filas")
        start += row_count


def split_csv(path: str, max_bytes: int, out_dir: str, label: str | None = None) -> None:
    base_name = os.path.splitext(os.path.basename(path))[0]
    file_prefix = f"{base_name}_{label}" if label else base_name
    os.makedirs(out_dir, exist_ok=True)

    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)

        part_num = 1
        out_file = None
        writer = None
        current_size = 0

        def open_new_part():
            nonlocal out_file, writer, current_size, part_num
            if out_file:
                out_file.close()
            part_path = os.path.join(out_dir, f"{file_prefix}_parte{part_num:02d}.csv")
            out_file = open(part_path, "w", newline="", encoding="utf-8")
            writer = csv.writer(out_file)
            writer.writerow(header)
            current_size = out_file.tell()
            print(f"Creando {part_path}")

        open_new_part()

        for row in reader:
            row_buffer = io.StringIO()
            csv.writer(row_buffer, lineterminator="\r\n").writerow(row)
            line = row_buffer.getvalue()
            line_size = len(line.encode("utf-8"))

            if current_size + line_size > max_bytes:
                part_num += 1
                open_new_part()

            writer.writerow(row)
            current_size += line_size

        out_file.close()


def main():
    parser = argparse.ArgumentParser(description="Divide CSV en partes por tamano maximo.")
    parser.add_argument("archivos", nargs="+", help="Rutas de los archivos CSV a dividir")
    parser.add_argument("--max-mb", type=float, default=18, help="Tamano maximo por parte en MB (default: 18)")
    parser.add_argument("--parts", type=int, help="Numero exacto de partes equilibradas")
    parser.add_argument("--label", help="Etiqueta que se agrega al nombre de cada parte")
    parser.add_argument("--out-dir", default="csv_partes", help="Carpeta de salida (default: csv_partes)")
    args = parser.parse_args()

    for archivo in args.archivos:
        if args.parts is not None:
            split_csv_parts(archivo, args.parts, args.out_dir)
        else:
            max_bytes = int(args.max_mb * 1024 * 1024)
            split_csv(archivo, max_bytes, args.out_dir, args.label)


if __name__ == "__main__":
    main()
