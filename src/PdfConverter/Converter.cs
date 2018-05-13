using System;
using System.CodeDom.Compiler;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Text.RegularExpressions;
using org.apache.pdfbox.pdmodel;
using org.apache.pdfbox.util;

namespace MTA.PdfConverter
{
  public static class Converter
  {
    private const string SentencesPattern = @"((?:(?(?=(\d+?\.\d|\.?\s+?[А-ЯA-Z]\.|\p{P}{2}\s+?[а-яa-z\d]))\2|[^.!?])+[.!?]?))";
    private const string PunctuationPattern = @"[^а-яА-Яa-zA-Z]{2,}";
    private const string TrimPattern = @"^[^а-яА-Яa-zA-Z]+|[^а-яА-Яa-zA-Z]+$|\b[а-яА-Яa-zA-Z]{1,2}\b\s+?";

    private const int MinWords = 7;
    private const int MinLenght = 15;

    public static string GetTextFromFile(string path)
    {
      Console.WriteLine($"Stripping text from {path}...");

      PDDocument doc = null;
      try
      {
        doc = PDDocument.load(path);
        var stripper = new PDFTextStripper();
        return stripper.getText(doc);
      }
      finally
      {
        doc?.close();
      }
    }

    public static IEnumerable<string> GetSentences(string text)
    {
      Console.WriteLine("Searching for sentences...");
      var separator = " ";
      var match = Regex.Match(text, SentencesPattern, RegexOptions.IgnoreCase);
      while (match.Success)
      {
        var sentence = match.Value;
        if (sentence.IsSentence())
        {
          var formatted = sentence.Replace("-\r\n", string.Empty);
          formatted = Regex.Replace(formatted, PunctuationPattern, separator, RegexOptions.IgnoreCase);
          formatted = Regex.Replace(formatted, TrimPattern, string.Empty, RegexOptions.IgnoreCase);

          if (formatted.IsSentence())
            yield return formatted.ToLower();
        }

        match = match.NextMatch();
      }
    }

    public static void FileToSentences(string from, string to)
    {
      var file = $"{Path.GetFileNameWithoutExtension(from)}.gz";
      var path = Path.Combine(to, file);

      using (var stream = new FileStream(path, FileMode.OpenOrCreate))
      using (var zip = new GZipStream(stream, CompressionLevel.Fastest))
      using (var writer = new StreamWriter(zip))
      {
        foreach (var sentence in Converter.GetSentences(Converter.GetTextFromFile(from)))
          writer.WriteLine(sentence);
      }
    }

    public static void DirectoryToSentences(string from, string to)
    {
      var files = Directory.GetFiles(from, "*.pdf");

      foreach (var file in files)
        Converter.FileToSentences(file, to);
    }

    private static int WordsCount(this string text) => text.Split(null).Length;

    private static bool IsSentence(this string text) => 
      text.WordsCount() > Converter.MinWords && 
      text.Length > Converter.MinLenght;
  }
}
