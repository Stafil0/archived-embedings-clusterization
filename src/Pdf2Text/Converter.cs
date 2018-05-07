using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using org.apache.pdfbox.pdmodel;
using org.apache.pdfbox.util;

namespace MTA.Pdf2Text
{
  public static class Converter
  {
    private static readonly string[] Inlines = { "лат", "греч", "т", "др", "англ", "см", "нм", "тыс", "R" };
    private static readonly char[] Endlines = {',', '.', ' ', '?', '!'};
    
    private static readonly string MatchesRegex = $@"((?:(?(?=(\b{string.Join(@"\.|\b", Inlines)}\.|\d+\.\d))\2|[^.!?])+[.!?]))";
    private const string FormattedRegex = @"[^а-€ј-яa-zA-Z]{2,}";

    public static IEnumerable<string> GetSentences(string path)
    {
      PDDocument doc = null;

      try
      {
        doc = PDDocument.load(path);
        var stripper = new PDFTextStripper();
        var text = stripper.getText(doc);
        var separator = stripper.getWordSeparator();

        var match = Regex.Match(text, MatchesRegex, RegexOptions.IgnoreCase);
        while (match.Success)
        {
          if (match.Length > 10)
          {
            var formatted = Regex.Replace(match.Value, FormattedRegex, separator, RegexOptions.IgnoreCase)
                                 .Trim(Endlines)
                                 .ToLower();

            if (formatted.Length > 10)
              yield return formatted;
          }
          match = match.NextMatch();
        }
      }
      finally
      {
        doc?.close();
      }
    }

    public static void ToSetntencesFile(string from, string to)
    {
      using (var writer = new StreamWriter(to))
      {
        foreach (var sentence in Converter.GetSentences(from))
          writer.WriteLine(sentence);
      }
    }
  }
}
