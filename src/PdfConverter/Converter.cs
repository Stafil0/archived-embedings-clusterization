using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using org.apache.pdfbox.pdmodel;
using org.apache.pdfbox.util;

namespace MTA.PdfConverter
{
  public static class Converter
  {
    private static readonly string[] Inlines = { "лат", "греч", "др", "англ", "см", "нм", "тыс", "ат" };
    private static readonly char[] TrimSymbols = { ',', '.', ' ', '?', '!', '-', '—', '＿' };
    private static readonly string MatchesRegex = $@"((?:(?(?=(\b{string.Join(@"\.|\b", Inlines)}\.|[^а-яА-Яa-zA-Z][а-яА-Яa-zA-Z]\.\s?|\d+\.\d))\2|[^.!?])+[.!?]))";
    private const string PunctuationRegex = @"[^а-яА-Яa-zA-Z]{2,}";
    private const string ShortWordsRegex = @"\b[а-яА-Яa-zA-Z]{1,2}\b";

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

    public static IEnumerable<string> GetTextFromDirectory(string path)
    {
      var files = Directory.GetFiles(path, "*.pdf");
      Console.WriteLine($"Working with directory {path}...");

      for (int i = 0; i < files.Length; i++)
      {
        Console.WriteLine($"Done {i}/{files.Length} files...");
        yield return Converter.GetTextFromFile(files[i]);
      }
    }

    public static IEnumerable<string> GetSentences(string text)
    {
      Console.WriteLine("Searching for sentences...");
      var separator = " ";
      var match = Regex.Match(text, MatchesRegex, RegexOptions.IgnoreCase);
      while (match.Success)
      {
        var sentence = match.Value;
        if (sentence.IsSentence())
        {
          var formatted = sentence.Replace("-\r\n", string.Empty);
          formatted = Regex.Replace(formatted, PunctuationRegex, separator, RegexOptions.IgnoreCase);
          formatted = Regex.Replace(formatted, ShortWordsRegex, string.Empty, RegexOptions.IgnoreCase);
          formatted = formatted.ToLower().Trim(TrimSymbols);

          if (formatted.IsSentence())
            yield return formatted;
        }

        match = match.NextMatch();
      }
    }

    public static void FileToSentences(string file, string savePath)
    {
      using (var writer = new StreamWriter(savePath, true))
      {
        var text = Converter.GetTextFromFile(file);
        foreach (var sentence in Converter.GetSentences(text))
          writer.WriteLine(sentence);
      }
    }

    public static void DirectoryToSentences(string directory, string savePath)
    {
        foreach (var text in Converter.GetTextFromDirectory(directory))
        foreach (var sentence in Converter.GetSentences(text))
          Console.WriteLine(sentence);
    }

    private static int WordsCount(this string text) => text.Split(null).Length;
    private static bool IsSentence(this string text) => text.WordsCount() > 3 && text.Length > 15;
  }
}
