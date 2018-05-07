using System.Collections.Generic;
using System.Text.RegularExpressions;
using org.apache.pdfbox.pdmodel;
using org.apache.pdfbox.util;

namespace MTA.Pdf2Text
{
  public static class Converter
  {
    private const string Space = " ";

    public static IEnumerable<string> ParsePdf(string path)
    {
      PDDocument doc = null;

      try
      {
        doc = PDDocument.load(path);
        var stripper = new PDFTextStripper();

        return Regex.Replace(stripper.getText(doc), @"\b[\d\W]+\b", Space);
      }
      finally
      {
        doc?.close();
      }
    }
  }
}
