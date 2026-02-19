import os
import re
import fitz
from pathlib import Path
from typing import List, Optional
from unstructured.partition.auto import partition
from unstructured.cleaners.core import clean_bullets
from html2text import html2text

class PDFParser:
    """
    A class to parse PDF files into Markdown and extract images using unstructured and fitz.
    """
    def __init__(self, output_dir: str, ocr_engine: str = "paddleocr", languages: List[str] = ["chi_sim", "eng"]):
        self.output_dir = Path(output_dir)
        self.ocr_engine = ocr_engine
        self.languages = languages

        # Patterns from original script
        self.title_pattern = re.compile(r'^(\d+(?:\.\d+)*)\s+(.*)$')
        self.header_chapter_pattern = re.compile(r'^第(\d+)章\s*(.*?)\s*(\d+)$')

    def _setup_env(self):
        """Optional environment setup for poppler/tesseract on macOS."""
        if os.path.exists("/opt/homebrew/bin"):
            os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ["PATH"]

    def _get_image(self, element, page):
        """Extracts an image from a PDF page based on element coordinates."""
        try:
            coord_system = element.metadata.coordinates.system
            u_page_width = coord_system.width
            u_page_height = coord_system.height
            points = element.metadata.coordinates.points

            # (x0, y0, x1, y1)
            u_x0, u_y0 = points[0]
            u_x1, u_y1 = points[2]

            # Relative positions
            rel_x0 = u_x0 / u_page_width
            rel_y0 = u_y0 / u_page_height
            rel_x1 = u_x1 / u_page_width
            rel_y1 = u_y1 / u_page_height

            # Map to Fitz page dimensions
            f_page_width = page.rect.width
            f_page_height = page.rect.height

            offset_x = page.rect.x0
            offset_y = page.rect.y0

            final_x0 = (rel_x0 * f_page_width) + offset_x
            final_y0 = (rel_y0 * f_page_height) + offset_y
            final_x1 = (rel_x1 * f_page_width) + offset_x
            final_y1 = (rel_y1 * f_page_height) + offset_y

            # Fitz cropping with adjustments from original script
            fix_x = 8
            fix_y = 8
            rect = fitz.Rect(final_x0 - fix_x, final_y0 - fix_y - 1, final_x1 + fix_x, final_y1 + fix_y + 18)
            rect = rect & page.rect

            if rect.width < 1 or rect.height < 1:
                return None

            zoom = 2
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, clip=rect)

            if pix.width < 1 or pix.height < 1:
                return None

            return pix
        except Exception as e:
            print(f"Error extracting image: {e}")
            return None

    def parse(self, pdf_path: str, book_name: Optional[str] = None, chapter: Optional[str] = None) -> str:
        """
        Parses the given PDF file and saves Markdown and images to the output directory.
        Returns the path to the generated Markdown file.
        """
        self._setup_env()

        pdf_path_obj = Path(pdf_path)
        if book_name is None:
            book_name = pdf_path_obj.parent.name
        if chapter is None:
            chapter = pdf_path_obj.stem

        # Create output directories
        book_output_dir = self.output_dir / book_name
        img_output_dir = book_output_dir / "imgs"
        img_output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Partition PDF using unstructured
        print(f"Partitioning PDF: {pdf_path}")
        elements = partition(
            filename=pdf_path,
            strategy="hi_res",
            infer_table_structure=True,
            languages=self.languages,
            ocr_engine=self.ocr_engine,
        )

        # 2. Open PDF with fitz for image extraction
        doc = fitz.open(pdf_path)

        md_lines = []
        image_count = 0
        prev_element_is_list = False

        print(f"Processing {len(elements)} elements...")
        for el in elements:
            cat = el.category
            pn = el.metadata.page_number
            text = el.text

            if cat == "Title":
                level = text.count('.') + 1
                if level > 1:
                    md_lines.append("#" * level + f" {text}\n")
                else:
                    md_lines.append(f"# {text}\n")
                print("#" * level + f" {text}\n")

            elif cat == "Header":
                # Skip headers as per original script behavior (prints but doesn't add to MD)
                continue

            elif cat == "Table":
                # Original script used 'XTable' but also handled 'Table' in image extraction
                # Unstructured usually marks it as 'Table' and might provide 'text_as_html'
                if hasattr(el.metadata, 'text_as_html') and el.metadata.text_as_html:
                    md_lines.append(html2text(el.metadata.text_as_html) + "\n")
                else:
                    # If it's a table but no HTML, try extracting it as an image
                    image_count += 1
                    page = doc[pn - 1]
                    pix = self._get_image(el, page)
                    if pix:
                        img_rel_path = f"imgs/chapter{chapter}-page{pn}_img{image_count}.png"
                        img_path = book_output_dir / img_rel_path
                        pix.save(str(img_path))
                        md_lines.append(f"![Table](./{img_rel_path})\n")
                    else:
                        md_lines.append(text + "\n")

            elif cat == "Image":
                image_count += 1
                page = doc[pn - 1]
                pix = self._get_image(el, page)
                if pix:
                    img_rel_path = f"imgs/chapter{chapter}-page{pn}_img{image_count}.png"
                    img_path = book_output_dir / img_rel_path
                    pix.save(str(img_path))
                    md_lines.append(f"![Image](./{img_rel_path})\n")

            elif cat == "ListItem":
                md_lines.append("- " + clean_bullets(text) + "\n")
                prev_element_is_list = True

            elif cat == "NarrativeText":
                if prev_element_is_list:
                    md_lines.append("\n")
                    prev_element_is_list = False
                md_lines.append(text + "\n")

            else:
                # Handle cases where title might be miscategorized
                if self.title_pattern.match(text):
                    level = text.count('.') + 1
                    if level > 1:
                        md_lines.append("#" * level + f" {text}\n")
                    else:
                        md_lines.append(f"# {text}\n")
                elif self.header_chapter_pattern.match(text):
                    # Skip chapter headers as per original script
                    continue
                else:
                    md_lines.append(text + "\n")

        doc.close()

        output_md_path = book_output_dir / f"{chapter}.md"
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write("".join(md_lines))

        print(f"Finished parsing. Output saved to: {output_md_path}")
        return str(output_md_path)
