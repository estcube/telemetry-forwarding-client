"""Main entrypoint file for the Telemetry decoder."""

import os
import sys
import logging
import time
import kiss
from ax_listener import AXListener, AXFrame
from conf import Configuration
from db_interface import TelemetryDB


def print_frame(frame: AXFrame):
    """Debug function that just prints the AXFrame object emitted by the AXListener."""
    print(frame)


def main():
    """Main loop function."""

    # Read in the client configuration.
    conf_path = os.path.join(os.path.dirname(__file__), "../configuration.ini")
    conf = Configuration(conf_path)

    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger(__name__)

    # Build the components.
    ax_listener = AXListener()

    db_loc = os.path.join(os.path.dirname(__file__), conf.get_conf("Client", "database"))
    database = TelemetryDB(db_loc)
    database.init_db()

    # Hook the callbacks to the ax_listener.
    ax_listener.add_callback(print_frame)
    ax_listener.add_callback(database.insert_ax_frame)

    k = kiss.TCPKISS(
        conf.get_conf("TNC interface", "tnc-ip"),
        conf.get_conf("TNC interface", "tnc-port"), strip_df_start=True
        )

    # Open the connection to the TNC.
    conn_tries = 0
    max_conn_tries = int(conf.get_conf("TNC interface", "max-connection-attempts"))
    retry_time = int(conf.get_conf("TNC interface", "connection-retry-time"))
    while True:
        try:
            k.start()
            break
        except ConnectionRefusedError:
            _logger.error(
                "Could not initialize a TCP connection to %s:%s",
                conf.get_conf("TNC interface", "tnc-ip"),
                conf.get_conf("TNC interface", "tnc-port")
                )
            if conn_tries < max_conn_tries:
                conn_tries = conn_tries + 1
                _logger.info("Retrying TNC connection in %d seconds...", retry_time)
                time.sleep(retry_time)
            else:
                _logger.error("Maximum TNC connection retries reached. Exiting...")
                sys.exit(-1)


    try:
        k.read(callback=ax_listener.receive)
    except KeyboardInterrupt:
        pass
    k.stop()


if __name__ == "__main__":
    main()
