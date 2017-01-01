import re

def get_pi_revision():
    """ Gets the version number of the Raspberry Pi board """
    # Revision list available at: http://elinux.org/RPi_HardwareHistory#Board_Revision_History
    try:
        with open('/proc/cpuinfo', 'r') as infile:
            for line in infile:
                # Match a line of the form "Revision : 0002" while ignoring extra
                # info in front of the revsion (like 1000 when the Pi was over-volted).
                match = re.match('Revision\s+:\s+.*(\w{4})$', line)
                if match and match.group(1) in ['0000', '0002', '0003']:
                    # Return revision 1 if revision ends with 0000, 0002 or 0003.
                    return 1
                elif match:
                    # Assume revision 2 if revision ends with any other 4 chars.
                    return 2
            # Couldn't find the revision, assume revision 0 like older code for compatibility.
            return 0
    except:
        return 0
