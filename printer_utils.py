import usb.backend.libusb1
import usb.core
import usb.util
import logging

from escpos.printer import Usb


PRINTER_VENDOR_ID = 0x0416
PRINTER_PRODUCT_ID = 0x5011
PRINTER_CHAR_WIDTH = 48
PRINTER_WIDTH_PX = 640
PRINTER_DPI = 203  # Usually 203 DPI = 8 dots/mm


_PRINTER = None

logger = logger = logging.getLogger("uvicorn") 
logger.setLevel(logging.INFO)


class PrinterError(Exception):
    pass


def _log(message, verbose):
  _log(message, verbose, level="info")
        
def _log(message, verbose, level="info"):
    if not verbose:
        return

    if level == "info":
        logger.info("prt - " + message)
    elif level == "warning":
        logger.warning("prt - " + message)
    elif level == "error":
        logger.error("prt - " + message)
    else:
        logger.info("prt - " + message)


def find_printer(verbose=True, stream_mode=False, force_refresh=False):
    """
    Returns cached printer or discovers it.
    """

    global _PRINTER

    if _PRINTER is not None and not force_refresh:
        return _PRINTER

    printer = _discover_printer(verbose=verbose, stream_mode=stream_mode)

    try:
        printer._raw(b'\x1b\x40')  # ESC @ initialize
        _log("Printer initialized.", verbose)
    except Exception as e:
        raise PrinterError(f"Failed to initialize printer: {e}")

    _PRINTER = printer
    return _PRINTER

def _discover_printer(verbose=True, stream_mode=False):
    backend = usb.backend.libusb1.get_backend()
    devices = usb.core.find(find_all=True, backend=backend)

    if devices is None:
        raise PrinterError("No USB devices found.")

    for device in devices:
        try:
            vendor_id = device.idVendor
            product_id = device.idProduct

            if vendor_id == PRINTER_VENDOR_ID and product_id == PRINTER_PRODUCT_ID:
                _log(f"Printer found: {hex(vendor_id)}:{hex(product_id)}", verbose)

                device.set_configuration()

                for cfg in device:
                    for intf in cfg:
                        try:
                            usb.util.claim_interface(device, intf.bInterfaceNumber)

                            endpoint = usb.util.find_descriptor(
                                intf,
                                custom_match=lambda e:
                                    usb.util.endpoint_direction(e.bEndpointAddress)
                                    == usb.util.ENDPOINT_OUT
                            )

                            if endpoint:
                                return Usb(
                                    vendor_id,
                                    product_id,
                                    intf.bInterfaceNumber,
                                    0,
                                    backend=backend
                                )

                        except usb.core.USBError as e:
                            _log(f"Could not claim interface {intf.bInterfaceNumber}: {e}", verbose)
                            continue

                raise PrinterError("Printer found but no valid OUT endpoint.")

        except usb.core.USBError as e:
            raise PrinterError(f"USB error while scanning devices: {e}")

    raise PrinterError("No matching USB printer found.")


def send_raw(printer, data: bytes): #BROKEN!
    """
    Send raw ESC/POS bytes to the printer.
    Works with escpos.printer.Usb and other escpos printers.
    """
    # Preferred: use the _raw() method if available (all escpos printers have it)
    if hasattr(printer, "_raw") and callable(printer._raw):
        printer._raw(data)
    else:
        # Fallback for very low-level USB objects
        if not hasattr(printer, "device"):
            raise RuntimeError("Printer object has no _raw method and no device attribute.")
        cfg = printer.device[0]             # first configuration
        intf = cfg[(0, 0)]                  # first interface, alt 0
        ep_out = intf[0]                     # first OUT endpoint
        printer.device.write(ep_out.bEndpointAddress, data)


def reset_printer(verbose=True):
    global _PRINTER

    if _PRINTER:
        try:
            _PRINTER.close()
            _log("Printer connection closed.", verbose)
        except Exception:
            pass

    _PRINTER = None
    
def cut_paper(verbose=True):
    try:
        printer = find_printer(verbose=verbose)
        printer.cut()
        _log("Paper cut completed.", verbose)
    except Exception as e:
        reset_printer(verbose=verbose)
        raise PrinterError(f"Failed to cut paper: {e}")