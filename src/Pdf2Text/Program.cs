using System;

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
      var path = @"D:\For work\Projects\MTA\Book.pdf";
      var output = Converter.ParsePdf(path);
    }
  }
}
