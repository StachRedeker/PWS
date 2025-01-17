import os
import yfinance as stocks
import math
import time
import signal
import sys

from utils import Utils

from matplotlib import pyplot as plt
from matplotlib import ticker as pltticker

from enum import Enum


class GraphSettings:
    def __init__(self, a, b, c, d=True, e=True):
        self.label = a
        self.period = b
        self.interval = c
        self.show_time = d
        self.show_date = e


class GraphType(Enum):
    # day/week/month/halfyear/year
    DAY = GraphSettings("day", "1d", "1m", True, False)
    WEEK = GraphSettings("week", "5d", "5m")
    MONTH = GraphSettings("month", "1mo", "1d")
    HALFYEAR = GraphSettings("halfyear", "6mo", "1d", False)
    YEAR = GraphSettings("year", "1y", "5d", False)


class StockProgram:
    # Waardes initialiseren
    def __init__(self):
        self.run = True
        self.commands = Commands(self)

        # Voor de 'watch'-functie
        self.watching_tick = None
        self.watching_name = None
        self.watching_info = None
        self.watching_last_update = time.time()
        self.watching_last_price = "0.00"

        # Instellingen
        self.watching_log = False

        signal.signal(signal.SIGINT, self.signal_handler)

    def reset_watching(self):
        self.watching_tick = None
        self.watching_name = None
        self.watching_info = None
        self.watching_last_update = time.time()
        self.watching_last_price = "0.00"

    # Het programma wordt geactiveerd als dit runt.
    def start(self):
        while self.run:
            if self.watching_tick is not None:
                if time.time() - self.watching_last_update >= 5.0:
                    self.watching_last_update = self.watching_last_update + 100
                    self.watchedloop()
            else:
                self.commandloop()

    def watchedloop(self):
        # De geschiedenis van de prijs van de afgelopen 2 dagen.
        history = self.watching_tick.history(period="2d")

        price_last_close = Utils.format_money(history.get("Close")[0])
        price_now = Utils.format_money(history.get("Close")[1])

        diff_previous_check = Utils.get_price_diff(price_now, self.watching_last_price)
        diff_last_close = Utils.get_price_diff(price_now, price_last_close)

        if not self.watching_log:
            print(
                "Current value " + self.watching_name + ": " + price_now + " (" + diff_previous_check + " | " + diff_last_close + ")" +
                (" " * 8), end="\r", flush=True)
        else:
            print(
                "Current value " + self.watching_name + ": " + price_now + " (" + diff_previous_check + " | " + diff_last_close + ")")

        self.watching_last_update = time.time()
        self.watching_last_price = price_now

    def commandloop(self):
        command_raw = input("Enter a command. ('help' for a list of commands)\n» ")
        command_split = command_raw.split(" ")
        command_name = command_split[0].lower()

        arguments = command_split.copy()
        arguments.pop(0)

        if command_name == "info":
            self.commands.info(arguments)
            return
        elif command_name == "watch":
            self.commands.watch(arguments)
        elif command_name == "watchlog":
            self.commands.watchlog(arguments)
            return
        elif command_name == "graph":
            self.commands.graph(arguments)
            return
        elif command_name in ["quit", "stop", "exit"]:
            self.commands.quit(arguments)
            return
        elif command_name == "help":
            self.commands.help(arguments)
            return
        else:
            Utils.unknown_command(command_name)

    def signal_handler(self, sig, frame):
        if self.watching_tick is not None:
            self.reset_watching()
            print("\nCancelled watching.\n")
        else:
            print("Goodbye!")
            sys.exit(0)


class Commands:
    def __init__(self, program):
        self.program = program

    def quit(self, arguments):
        self.program.run = False
        print("Goodbye!")

    def help(self, arguments):
        print("\nAvailable commands:")
        print("- help | View this list of commands.")
        print("- info <ticker> | View the information about a certain stock.")
        print("- watch <ticker> | Watch a stock's price. Updates every 5 seconds.")
        print("- graph <ticker> <period> [save] | Generate a graph for a ticker.")
        print("- watchlog | Toggles the logging style of the watch feature.")
        print("- stop,quit,exit | Stop the program.")
        print("<...>: required, [...]: optional\n")

    def graph(self, arguments):
        if len(arguments) >= 2:
            save = False
            if len(arguments) >= 3:
                if arguments[2].lower() in ["true", "yes", "ja"]:
                    save = True
                elif arguments[2].lower() not in ["false", "no", "nee"]:
                    print("Argument \"" + arguments[2] + "\" invalid. \nOptions: True, False")
                    return

            ticker_name = arguments[0].upper()
            period_name = arguments[1].upper()

            periods = [e.name for e in GraphType]

            if period_name in periods:
                # Periode bestaat.
                print("Fetching information about " + ticker_name + "...")
                stock_info = Utils.get_market_info(ticker_name)

                if stock_info is not None:
                    name = Utils.get_full_name(ticker_name, stock_info)

                    graph_settings = GraphType[period_name].value
                    print(
                        "Generating a graph for " + name + " of the last " + graph_settings.label + " (" + graph_settings.period + ") with an interval of " + graph_settings.interval + "... [0%]   ",
                        end="\r", flush=True)

                    ticker = stocks.Ticker(ticker_name)
                    history = ticker.history(graph_settings.period, graph_settings.interval)

                    data_times = []
                    data_closes = list(history.get("Close"))

                    for timestamp in history.index:
                        pydate = timestamp.to_pydatetime()

                        date_string = ""

                        if graph_settings.show_date:
                            date_string = date_string + Utils.format_time(pydate.day) + " " + Utils.months[
                                pydate.month - 1] + " " + str(pydate.year)
                            if graph_settings.show_time:
                                date_string = date_string + " - "

                        if graph_settings.show_time:
                            date_string = date_string + Utils.format_time(pydate.hour) + ":" + Utils.format_time(
                                pydate.minute)

                        data_times.append(date_string)

                    # Opruimen van NaN-waardes, noodzakelijk om problemen te voorkomen.
                    prev = 0
                    for i in range(len(data_times)):
                        # Compleet niet nodig, maar het is leuker om naar te kijken dan dat het in 0.1s klaar is ;)
                        # Hm, seems like a valid reason - Sander
                        time.sleep(0.01)

                        if math.isnan(data_closes[i]):
                            data_closes[i] = prev

                        prev = data_closes[i]

                        print(
                            "Generating a graph for " + name + " of the last " + graph_settings.label +
                            " (" + graph_settings.period + ") with an interval of " + graph_settings.interval +
                            "... [{0}%]      "
                            .format(round(float(i) / float(len(data_times) - 1) * 100, 2)),
                            end="\r", flush=True)

                    fig, ax = plt.subplots(nrows=1, ncols=1)
                    plt.subplots_adjust(bottom=0.15)

                    ax.set_title(name + " History - last " + graph_settings.period)

                    fig.set_size_inches(18.5, 10.5)
                    ax.plot_date(data_times, data_closes, marker='', linestyle='-')
                    ax.xaxis.set_major_locator(pltticker.MultipleLocator(5))

                    save_dir = "graphs/" + ticker_name + "_" + graph_settings.period + ".png"

                    if save and not os.path.isdir("graphs"):
                        os.makedirs("graphs")

                    fig.autofmt_xdate()

                    plt.show()

                    if save:
                        res = fig.savefig(save_dir)

                        if res is None:
                            file_path = os.path.realpath(__file__).split("\\")
                            file_path.pop()
                            print("\nGraph generated at \"{0}\"".format("/".join(file_path) + "/" + save_dir))
                        else:
                            print("An error occurred while generating the graph. Please try again. (" + str(
                                res) + ")")

                    plt.close(fig)
                    return
                else:
                    print("That ticker could not be recognised. Is it spelt correctly?")
                    return
            else:
                print("Period \"" + period_name.lower() + "\" invalid."
                                                          "\nOptions: " + str(periods).replace("[", "")
                      .replace("]", "").replace("'", "").lower())
                return
        else:
            print("Usage: graph <ticker> <period>")
            return

    def watchlog(self, arguments):
        if self.program.watching_log:
            self.program.watching_log = False
            print("Toggled logging style to a single line.")
        else:
            self.program.watching_log = True
            print("Toggled logging style to multiple lines.")

    def info(self, arguments):
        if len(arguments) > 0:
            ticker_name = arguments[0].upper()

            print("Fetching information about " + ticker_name + "...")
            stock_info = Utils.get_market_info(ticker_name)

            if stock_info is not None:
                # De markt bestaat
                titel = "================= Information " + ticker_name + " ================="
                print("\n" + titel + "\n")
                if "longName" in stock_info:
                    print(" " + stock_info["longName"] + " is a company in the " + stock_info["sector"] + " sector.")
                    print(
                        " It has an estimated amount of " + str(
                            stock_info["fullTimeEmployees"]) + " full-time employees.")
                print(" At this time, one share is worth " + Utils.format_money(
                    stocks.Ticker(ticker_name).history(period="1d").get("Close")[0]) + " " + stock_info["currency"] + ".")
                print("\n" + ("=" * len(titel)) + "\n")
            else:
                # De markt bestaat niet.
                print("That ticker could not be recognised. Is it spelt correctly?")
        else:
            print("Usage: info <ticker>")

    def watch(self, arguments):
        if len(arguments) > 0:
            ticker_name = arguments[0].upper()

            print("Fetching information about " + ticker_name + "...")

            stock_info = Utils.get_market_info(ticker_name)

            if stock_info is not None:
                name = Utils.get_full_name(ticker_name, stock_info)

                print("You are now watching " + name + ". (price in " + stock_info["currency"] + ")")
                self.program.watching_tick = stocks.Ticker(ticker_name)
                self.program.watching_name = ticker_name
                self.program.watching_info = stock_info
                self.program.watching_last_price = "0.00"
            else:
                print("That ticker could not be recognised. Is it spelt correctly?")
        else:
            print("Usage: watch <ticker>")