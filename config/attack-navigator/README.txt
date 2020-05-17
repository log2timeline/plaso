Plaso windows tagging: tag_windows.txt
Check coverage MITRE ATTACK (see comment):https://mitre-attack.github.io/attack-navigator/enterprise/#layerURL=https%3A%2F%2Fraw.githubusercontent.com%2Flog2timeline%2Fplaso%2Fmaster%2Fdata%2Fplaso_tagging_windows_coverage_mitre.json
Information on tag user_suspect_file:
 - Check in c:\users
 - Check suspects files (date close of incident): 
   - Executable file: *.exe,*.dll, *.sys, *.scr, *.pif, *.com, *.ms [like msi/msp]
   - Archive file: *.zip,*.rar, *.cab, *.sfx
   - Script file: *.cmd, *.vb*, *.hta, *.ps*, *.ws*, *.py, *.js, *.bat, *.ms* [like msh powershell]
   - Document file (can be exploited player, use embedded file, internal script, ...): *.rtf,*.pdf,*.doc*,*.ppt*,*.xls*, *.otf
   - Special file player (can be exploited player or use capacity [clickonce]): *.jar, *.swf, *.jnlp, *.gadget, *.appref-ms,*.application
   - File can modify system configuration: *.reg
   - Regsvr32 [T1117]: *.sct
   - CMSTP [T1191]: *.inf
   - Control Panel Items[T1196]: *.cpl
   - Application shimming [T1138]: *.sdb
   - Forced Auth[T1187]: *.lnk, *.scf
   - Compiled HTML File [T1223]: *.chm
   - User execution[T1204] and Shortcut Modification[T1023]: *.lnk
   - File can be suspect (according by context: like bits): *.tmp
   - File htm can contains script or exploit for player: .[xm]htm[l]
   - java history: *.idx
