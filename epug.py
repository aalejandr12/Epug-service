import sys
import uuid
import tempfile
import shutil
import subprocess
from pathlib import Path

from natsort import natsorted
from ebooklib import epub
from PIL import Image

# ====== AJUSTA AQUÍ SI TU 7-ZIP ESTÁ EN OTRA RUTA ======
SEVEN_ZIP = r"C:\Program Files\7-Zip\7z.exe"
# Guardar EPUB intermedio (con TODAS las páginas) además del final
KEEP_BASE = False

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

def pedir_ruta_si_falta():
    if len(sys.argv) >= 2:
        return Path(sys.argv[1]).expanduser().resolve()
    ruta = input("Pega la ruta de la carpeta con tus .cbr: ").strip('"').strip()
    return Path(ruta).expanduser().resolve()

def verificar_7z():
    p = Path(SEVEN_ZIP)
    if not p.exists():
        raise FileNotFoundError(
            f"No se encontró 7z.exe en: {SEVEN_ZIP}\n"
            "Edita SEVEN_ZIP al inicio del script con la ruta correcta."
        )

def extraer_cbr_con_7z(cbr_path: Path, destino: Path):
    # 7z x "archivo.cbr" -o"destino" -y
    cmd = [SEVEN_ZIP, "x", str(cbr_path), f"-o{destino}", "-y"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"7z falló al extraer {cbr_path.name}:\n{res.stderr or res.stdout}")

def listar_imagenes(dir_):
    imgs = []
    for p in Path(dir_).rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            imgs.append(p)
    return natsorted(imgs, key=lambda x: x.name)

def leer_bytes(path_img: Path) -> bytes:
    with open(path_img, "rb") as f:
        return f.read()

def page_xhtml(idx: int, img_rel_path: str) -> epub.EpubHtml:
    page = epub.EpubHtml(
        title=f"Página {idx}",
        file_name=f"text/{idx:04d}.xhtml",
        lang="es",
    )
    page.content = f"""\
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><meta charset="utf-8"/></head>
  <body style="margin:0;padding:0;background:#000;">
    <div style="text-align:center;">
      <img src="../{img_rel_path}" alt="Página {idx}" style="max-width:100%;height:auto;"/>
    </div>
  </body>
</html>"""
    return page

def build_epub_con_todo(nombre: str, imgs: list[Path], destino: Path) -> Path:
    """Fase 1: crea un EPUB con TODAS las páginas (sin portada especial)."""
    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(nombre)
    book.set_language("es")

    chapters = []
    for i, img_path in enumerate(imgs, start=1):
        ext = img_path.suffix.lower()
        mime = MIME_MAP.get(ext, "image/jpeg")
        img_rel = f"images/{i:04d}{ext}"
        img_item = epub.EpubItem(file_name=img_rel, content=leer_bytes(img_path), media_type=mime)
        book.add_item(img_item)

        xhtml = page_xhtml(i, img_rel)
        book.add_item(xhtml)
        chapters.append(xhtml)

    book.toc = tuple(chapters)
    book.spine = ["nav"] + chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    out_path = destino / f"{nombre}._base.epub"
    epub.write_epub(str(out_path), book)
    return out_path

def build_epub_final(nombre: str, imgs: list[Path], destino: Path) -> Path:
    """Fase 2: quita la 1.ª página del interior y la usa como portada; genera EPUB final."""
    portada = imgs[0]
    paginas = imgs[1:]

    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(nombre)
    book.set_language("es")

    portada_ext = portada.suffix.lower()
    book.set_cover(f"cover{portada_ext}", leer_bytes(portada))

    chapters = []
    for i, img_path in enumerate(paginas, start=1):
        ext = img_path.suffix.lower()
        mime = MIME_MAP.get(ext, "image/jpeg")
        img_rel = f"images/{i:04d}{ext}"
        img_item = epub.EpubItem(file_name=img_rel, content=leer_bytes(img_path), media_type=mime)
        book.add_item(img_item)

        xhtml = page_xhtml(i, img_rel)
        book.add_item(xhtml)
        chapters.append(xhtml)

    if not chapters:
        info = epub.EpubHtml(title="Contenido", file_name="text/0001.xhtml", lang="es")
        info.content = """\
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><meta charset="utf-8"/></head>
  <body><p>Este EPUB contiene solo la portada extraída del CBR original.</p></body>
</html>"""
        book.add_item(info)
        chapters.append(info)

    book.toc = tuple(chapters)
    book.spine = ["nav"] + chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    out_path = destino / f"{nombre}.epub"
    epub.write_epub(str(out_path), book)
    return out_path

def procesar_cbr(cbr_path: Path, salida_dir: Path):
    print(f"Procesando: {cbr_path.name}")
    tmpdir = Path(tempfile.mkdtemp(prefix="cbr2epub_"))
    try:
        extraer_cbr_con_7z(cbr_path, tmpdir)
        imagenes = listar_imagenes(tmpdir)
        if not imagenes:
            print(f"  No se encontraron imágenes en {cbr_path.name}. Omitido.")
            return

        nombre = cbr_path.stem

        # Fase 1: EPUB con todas las páginas
        base_path = build_epub_con_todo(nombre, imagenes, salida_dir)
        print(f"  EPUB base: {base_path}")

        # Fase 2: EPUB final (quitando 1.ª página del interior y usándola como portada)
        final_path = build_epub_final(nombre, imagenes, salida_dir)
        print(f"  EPUB final: {final_path}")

        if not KEEP_BASE:
            try:
                base_path.unlink(missing_ok=True)
            except Exception:
                pass

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def main():
    verificar_7z()
    raiz = pedir_ruta_si_falta()
    if not raiz.exists() or not raiz.is_dir():
        print("La ruta no existe o no es una carpeta.")
        sys.exit(1)

    cbrs = [p for p in raiz.iterdir() if p.is_file() and p.suffix.lower() == ".cbr"]
    if not cbrs:
        print("No se encontraron archivos .cbr en esa carpeta.")
        return

    for cbr in natsorted(cbrs, key=lambda x: x.name):
        try:
            procesar_cbr(cbr, raiz)
        except Exception as e:
            print(f"  Error procesando {cbr.name}: {e}")

if __name__ == "__main__":
    main()
