using System;
using System.IO;

namespace MTA.PdfConverter
{
  class Program
  {
    /// <summary>
    /// The main entry point for the application.
    /// </summary>
    [STAThread]
    public static void Main(string[] args)
    {
      var path = Directory.GetCurrentDirectory();
      var samples = Path.GetFullPath(Path.Combine(path, @"..\..\..\..\samples"));
      var result = Path.Combine(samples, "sentences.txt");

      Converter.DirectoryToSentences(samples, result);
    }
  }
}
