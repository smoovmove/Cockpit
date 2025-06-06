# notes.py

import os 
import subprocess

from pathlib import Path

from datetime import datetime

from state import append_to_state_list

default_note_template = """=========================================================================

[System Info]
OS: 
Hostname: 
IP: 
Web Technology: 
Users:

=========================================================================

[Credentials]:

=========================================================================

[Quick Notes]:

=========================================================================

[NMAP RESULTS]:

=========================================================================

[Web Services Enumeration]:

=========================================================================

Take Away Concepts (for the flat-file reference system):
* 
* 
* 
"""

def open_notes(boxname: str, outdir: Path):
    notes_path = outdir / f"{boxname}_notes.txt"

    editor = os.environ.get("EDITOR", "micro")

    print(f"[*] Opening notes for {boxname} in {editor}... (close the editor to return to JARVIS)")

    try: 
        subprocess.run(
            [editor, str(notes_path)]
        )
    except FileNotFoundError: 
        print(f"[!] Editor {editor} not found. Falling back to nano...")

        try: 
            subprocess.run(
                ["nano", str(notes_path)]
            )
        except FileNotFoundError: 
            print("[!] No terminal editor foud. Please install nano.")


#this replaces the entire section in question 
def update_notes_section(notes_path: Path, section_header: str, new_content: str):
    if not notes_path.exists():
        print(f"[!] Notes file not found at {notes_path}")
    
    lines = notes_path.read_text().splitlines(keepends=True)

    updated_lines = []
    inside_target_section = False
    section_found = False

    for idx, line in enumerate(lines):
        stripped_line = line.strip()
        
        if stripped_line == section_header:  
            section_found = True
            inside_target_section = True
            updated_lines.append(line) #keep the header itself
            # Add new content with trailing newlines
            updated_lines.append(new_content.strip() + "\n\n")
            continue

        if inside_target_section and stripped_line.startswith("="): 
            if line.strip().startswith("[") and line.strip() != section_header: 
                #reached the next section
                inside_target_section = False
                updated_lines.append(line)
                continue
            
        if inside_target_section: 
            continue
        
        updated_lines.append(line)

    if not section_found: 
        print(f"[!] Section header '{section_header}' not found in notes file")

    notes_path.write_text("".join(updated_lines))

#this appends to the section in question 
def append_to_notes_section(notes_path: Path, section_header: str, new_content: str):
    if not notes_path.exists():
        print(f"[!] Notes file not found at {notes_path}")
    
    lines = notes_path.read_text().splitlines(keepends=True)

    updated_lines = []
    inside_target_section = False
    section_found = False
    content_appended = False
    temp_selection_content = []

    for i, line in enumerate(lines):

        stripped_line = line.strip()

        #Match the section header exactly
        if stripped_line == section_header: 
            section_found = True 
            inside_target_section = True 
            updated_lines.append(line)
            continue

        #If we are inside the target section
        if inside_target_section and stripped_line.startswith("="): 
            #if we hit the next section
            if not content_appended: 
                updated_lines.append(new_content.strip() + "\n\n")
                content_appended = True
                    
            inside_target_section = False
        
        #add the current line
        updated_lines.append(line)

        #if file ended while still inside target section, append at end
    if inside_target_section and not content_appended: 
        updated_lines.append(new_content.strip() + "\n\n")
        content_appended = True

    if not section_found: 
        print(f"[!] Section header '{section_header}' not found in notes file")

    notes_path.write_text("".join(updated_lines))


def extract_nmap_services(scan_file: Path) -> str: 
    if not scan_file.exists():
        return "[!] Scan file not found."
    
    extracted = []
    for line in scan_file.read_text().splitlines():
        if line and line[0].isdigit() and ("/tcp" in line or "/udp" in line): 
            parts = line.split()
            if "open" in parts: 
                # Find the index of "open"
                open_index = parts.index("open")

                #reconstruct everything from port/protocol up to the end 
                service_info = " ".join(parts[:open_index + 1]) 
            if len(parts) > open_index + 1:
                service_info += " " + " ".join(parts[open_index + 1]) # adds service and version

            extracted.append(" ".join(parts[:3])) #eg, "135/tcp open msrpc"

    return "\n".join(extracted) if extracted else "[!] No services found."

def extract_os_from_nmap(scan_file: Path) -> str: 
    if not scan_file.exists():
        return "[!] Scan file not found."
    
    lines = scan_file.read_text().splitlines()
    
    #try specific match from service info 
    for line in lines: 
        if line.startswith("Service Info:") and "OS:" in line: 
            try: 
                os_part = line.split("OS:")[1]
                os_value = os_part.split(";")[0].strip()
                return os_value
            except IndexError: 
                continue
    
    #fallback: keyword match
    os_keywords = ["Windows", "Linux", "Ubuntu", "Debian", "CentOS", "FreeBSD", "Unix", "Fedora"]
    for line in scan_file.read_text().splitlines(): 
        for keyword in os_keywords: 
            if keyword.lower() in line.lower():
                return line.strip()
            
    return "[!] No OS found."

def extract_web_tech(header_text: str) -> str: 
    header_lines = []
    for line in header_text.splitlines():
        if line.lower().startswith("server") or line.lower().startswith("x-powered-by:"):
            header_lines.append(line.strip())

    return "\n".join(header_lines) if header_lines else ""

def notes_quick(notes_path: Path):
    print("┌" + "─" * 46 + "┐")
    print("│ Write your note. Press ENTER twice to save.  │")
    print("└" + "─" * 46 + "┘")

    lines = []
    while True: 
        line = input("  > ").rstrip()
        if not line: 
            break
        lines.append(line)

    if not lines: 
        print("[-] Empty note. Nothing added.")
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    note = f"- [{timestamp}] {lines[0]}"
    for line in lines[1:]: 
        note += f"\n      {line}"

    append_to_notes_section(notes_path, "[Quick Notes]:", note)
    print("[+] Multi-line note added to [Quick Notes]")
    
    outdir = notes_path.parent
    append_to_state_list(outdir, "notes", {
        "timestamp": timestamp,
        "content": "\n".join(lines)
    })

def notes_creds(notes_path: Path):
    print("┌" + "─" * 46 + "┐")
    print("│ Enter a discovered credential.               │")
    print("└" + "─" * 46 + "┘")

    service = input("  Service (e.g., FTP, SSH): ").strip()
    username = input("  Username: ").strip()
    password = input("  Password: ").strip()

    if not (username and password):
        print("[-] Username and password are required. The credential hasn't been added.")
        return
    
    if service: 
        formatted_cred = f"- {service} → {username}:{password}"
    else: 
        formatted_cred = f"- {username}:{password}"

    append_to_notes_section(notes_path, "[Credentials]:", formatted_cred)
    print(f"[+] Credential added under [Credentials]")
    
    outdir = notes_path.parent
    append_to_state_list(outdir, "credentials", {
        "service": service or "unknown",
        "username": username,
        "password": password
    })

def notes_users(notes_path: Path):
    print("┌" + "─" * 46 + "┐")
    print("│ Enter a discovered username.                 │")
    print("│ Press ENTER twice to save.                   │")
    print("└" + "─" * 46 + "┘")

    users = []
    while True: 
        user = input("  > ").strip()
        if not user: 
            break
        users.append(f"- {user}")

    if not users: 
        print("[-] No users entered.")
        return
    
    append_to_notes_section(notes_path, "Users:", "\n".join(users))
    print(f"[+] {len(users)} user(s) added to Users")

