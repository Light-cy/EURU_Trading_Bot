#property script_show_inputs
#property description "Export historical MT5 bars as UTC-labelled CSV."

input string InpSymbol = "EURUSD";
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_M15;
input datetime InpFromUTC = D'2020.01.01 00:00';
input datetime InpToUTC = D'2025.12.31 23:59';

string MakeTimestampUTC(const datetime value)
{
   MqlDateTime parts;
   if(!TimeToStruct(value, parts))
      return "";

   return StringFormat(
      "%04d-%02d-%02dT%02d:%02d:00Z",
      parts.year,
      parts.mon,
      parts.day,
      parts.hour,
      parts.min
   );
}

void OnStart()
{
   if(InpSymbol == "")
   {
      Print("Export failed: symbol cannot be empty.");
      return;
   }

   if(InpFromUTC >= InpToUTC)
   {
      Print("Export failed: InpFromUTC must be earlier than InpToUTC.");
      return;
   }

   if(!SymbolSelect(InpSymbol, true))
   {
      PrintFormat(
         "Export failed: could not select symbol %s (error %d).",
         InpSymbol,
         GetLastError()
      );
      return;
   }

   long chartMode = SymbolInfoInteger(InpSymbol, SYMBOL_CHART_MODE);
   if(chartMode != SYMBOL_CHART_MODE_BID)
   {
      PrintFormat(
         "Export failed: %s is not configured for Bid chart prices.",
         InpSymbol
      );
      return;
   }

   int symbolDigits = (int)SymbolInfoInteger(InpSymbol, SYMBOL_DIGITS);
   double symbolPoint = SymbolInfoDouble(InpSymbol, SYMBOL_POINT);

   MqlRates rates[];
   ResetLastError();
   int copied = CopyRates(
      InpSymbol,
      InpTimeframe,
      InpFromUTC,
      InpToUTC,
      rates
   );

   if(copied <= 0)
   {
      PrintFormat(
         "Export failed: no history returned for %s (error %d). "
         "Load more chart history, check the symbol/date range, and retry.",
         InpSymbol,
         GetLastError()
      );
      return;
   }

   ArraySetAsSeries(rates, false);

   string timeframe = EnumToString(InpTimeframe);
   StringReplace(timeframe, "PERIOD_", "");
   string fromDate = TimeToString(InpFromUTC, TIME_DATE);
   string toDate = TimeToString(InpToUTC, TIME_DATE);
   StringReplace(fromDate, ".", "");
   StringReplace(toDate, ".", "");
   string fileName = StringFormat(
      "%s_%s_%s_%s_BID.csv",
      InpSymbol,
      timeframe,
      fromDate,
      toDate
   );

   ResetLastError();
   int file = FileOpen(
      fileName,
      FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON,
      ','
   );
   if(file == INVALID_HANDLE)
   {
      PrintFormat(
         "Export failed: could not create %s (error %d).",
         fileName,
         GetLastError()
      );
      return;
   }

   FileWrite(
      file,
      "time_utc",
      "open",
      "high",
      "low",
      "close",
      "tick_volume",
      "spread_points",
      "point"
   );

   for(int i = 0; i < copied; i++)
   {
      string timestamp = MakeTimestampUTC(rates[i].time);
      if(timestamp == "")
      {
         FileClose(file);
         FileDelete(fileName, FILE_COMMON);
         PrintFormat("Export failed: invalid bar timestamp at row %d.", i);
         return;
      }

      FileWrite(
         file,
         timestamp,
         DoubleToString(rates[i].open, symbolDigits),
         DoubleToString(rates[i].high, symbolDigits),
         DoubleToString(rates[i].low, symbolDigits),
         DoubleToString(rates[i].close, symbolDigits),
         (long)rates[i].tick_volume,
         rates[i].spread,
         DoubleToString(symbolPoint, 10)
      );
   }

   FileFlush(file);
   FileClose(file);

   PrintFormat(
      "Export complete: %d bars written to %s",
      copied,
      fileName
   );
   PrintFormat(
      "Returned history range: %s to %s",
      MakeTimestampUTC(rates[0].time),
      MakeTimestampUTC(rates[copied - 1].time)
   );
   PrintFormat(
      "File location: %s\\Files\\%s",
      TerminalInfoString(TERMINAL_COMMONDATA_PATH),
      fileName
   );
   Print(
      "Prices are the symbol's MT5 chart bars (normally Bid for forex); "
      "spread_points is the bar's broker-reported spread, not Ask OHLC."
   );
}
