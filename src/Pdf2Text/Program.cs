using System;
using System.IO;
using System.Linq;

namespace MTA.Pdf2Text
{
  class Program
  {
    /// <summary>
    /// The main entry point for the application.
    /// </summary>
    [STAThread]
    static void Main(string[] args)
    {
      var bookPath = @"D:\For work\Projects\MTA\Book.pdf";
      var txtPath = $@"{Path.GetDirectoryName(bookPath)}\{Path.GetFileNameWithoutExtension(bookPath)}.txt";
      Converter.ToSetntencesFile(bookPath, txtPath);
    }
  }
}
