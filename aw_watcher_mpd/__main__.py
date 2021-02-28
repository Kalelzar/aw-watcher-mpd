import argparse

from aw_core.log import setup_logging
from aw_watcher_mpd.mpd import MPDWatcher

def main() -> None:
    parser = argparse.ArgumentParser("A watcher for mpd to detect currently played song")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                    help="run with verbose logging")
    parser.add_argument("--testing", action="store_true",
                        help="run in testing mode")
    args = parser.parse_args()

    setup_logging("aw-watcher-mpd",
                  testing=args.testing, verbose=args.verbose,
                  log_stderr=True, log_file=True)

    watcher = MPDWatcher(testing=args.testing)
    watcher.run()

if __name__ == "__main__":
    main()
