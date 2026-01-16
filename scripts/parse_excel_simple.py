#!/usr/bin/env python3
"""
Parse list.csv (Excel file) to extract player, goalie, and coach data
Uses only standard library (zipfile, xml) - no external dependencies
"""
import zipfile
import xml.etree.ElementTree as ET
import json
import os

def parse_excel_data(filepath):
    """Parse the Excel file and extract all data"""
    data = {
        'players': [],
        'goalies': [],
        'coaches': []
    }
    
    with zipfile.ZipFile(filepath, 'r') as z:
        # Read shared strings
        with z.open('xl/sharedStrings.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            strings = []
            for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                strings.append(si.text if si.text else '')
        
        # Helper function to get cell value
        def get_cell_value(cell, strings):
            v = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
            if v is None or v.text is None:
                return None
            if cell.get('t') == 's':  # String reference
                return strings[int(v.text)]
            else:  # Number
                try:
                    return int(float(v.text))
                except:
                    return v.text
        
        # Parse Players (Sheet 1)
        print("Parsing Players...")
        with z.open('xl/worksheets/sheet1.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            
            rows = root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
            for row in rows[1:]:  # Skip header row
                cells = row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                if not cells:
                    continue
                
                row_data = {}
                for cell in cells:
                    cell_ref = cell.get('r')
                    col = ''.join([c for c in cell_ref if c.isalpha()])
                    val = get_cell_value(cell, strings)
                    row_data[col] = val
                
                if 'A' in row_data and row_data['A']:  # First name exists
                    first_name = row_data.get('A', '')
                    last_name = row_data.get('B', '')
                    name = f"{first_name} {last_name}".strip()
                    
                    player = {
                        'name': name,
                        'position': row_data.get('D', 'C'),
                        'type': row_data.get('G', ''),  # Player type (STYLE column - playmaker, sniper, etc.)
                        'era': row_data.get('F', ''),  # Era (column F)
                        'off': row_data.get('H', 75),
                        'def': row_data.get('I', 75),
                        'lead': row_data.get('J', 75),
                        'phys': row_data.get('K', 75),
                        'const': row_data.get('L', 75),
                    }
                    data['players'].append(player)
        
        # Parse Goalies (Sheet 2)
        print("Parsing Goalies...")
        with z.open('xl/worksheets/sheet2.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            
            rows = root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
            for row in rows[1:]:  # Skip header row
                cells = row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                if not cells:
                    continue
                
                row_data = {}
                for cell in cells:
                    cell_ref = cell.get('r')
                    col = ''.join([c for c in cell_ref if c.isalpha()])
                    val = get_cell_value(cell, strings)
                    row_data[col] = val
                
                if 'A' in row_data and row_data['A']:  # First name exists
                    first_name = row_data.get('A', '')
                    last_name = row_data.get('B', '')
                    name = f"{first_name} {last_name}".strip()
                    
                    goalie = {
                        'name': name,
                        'position': 'G',
                        'era': row_data.get('F', ''),  # Era (column F)
                        'gen': row_data.get('G', 80),  # GEN (column G)
                        'const': row_data.get('H', 80),  # CONST (column H)
                    }
                    data['goalies'].append(goalie)
        
        # Parse Coaches (Sheet 3)
        print("Parsing Coaches...")
        with z.open('xl/worksheets/sheet3.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            
            rows = root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
            for row in rows[1:]:  # Skip header row
                cells = row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                if not cells:
                    continue
                
                row_data = {}
                for cell in cells:
                    cell_ref = cell.get('r')
                    col = ''.join([c for c in cell_ref if c.isalpha()])
                    val = get_cell_value(cell, strings)
                    row_data[col] = val
                
                if 'A' in row_data and row_data['A']:  # First name exists
                    first_name = row_data.get('A', '')
                    last_name = row_data.get('B', '')
                    name = f"{first_name} {last_name}".strip()
                    
                    coach = {
                        'name': name,
                        'type': row_data.get('D', ''),  # Style (column D)
                        'era': row_data.get('C', ''),  # Era (column C)
                        'off': row_data.get('E', 75),  # OFF (column E)
                        'def': row_data.get('F', 75),  # DEF (column F)
                    }
                    data['coaches'].append(coach)
    
    return data

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(project_root, 'list.csv')
    output_path = os.path.join(project_root, 'data', 'sample_data.json')
    
    print(f"Parsing {excel_path}...")
    data = parse_excel_data(excel_path)
    
    print(f"\nFound:")
    print(f"  Players: {len(data['players'])}")
    print(f"  Goalies: {len(data['goalies'])}")
    print(f"  Coaches: {len(data['coaches'])}")
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nData saved to {output_path}")
    
    # Show sample data
    if data['players']:
        print(f"\nSample player: {data['players'][0]}")
    if data['goalies']:
        print(f"Sample goalie: {data['goalies'][0]}")
    if data['coaches']:
        print(f"Sample coach: {data['coaches'][0]}")

if __name__ == '__main__':
    main()
