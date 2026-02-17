#!/usr/bin/env python3
"""
RFQ Generator for Babipoly Board Game
Generates a professional Request for Quotation document from rfq.json
"""

import json
import base64
import os
from datetime import datetime
from pathlib import Path

# Set library path for macOS (needed for weasyprint/pango)
if os.path.exists('/opt/homebrew/lib'):
    os.environ['DYLD_LIBRARY_PATH'] = f"/opt/homebrew/lib:{os.environ.get('DYLD_LIBRARY_PATH', '')}"


class RFQGenerator:
    def __init__(self, json_file='rfq.json', logo_file='logo.jpg'):
        with open(json_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.date = datetime.now().strftime('%B %d, %Y')
        self.logo_base64 = self._encode_logo(logo_file)

    def _encode_logo(self, logo_file):
        """Encode logo image to base64 for embedding in HTML"""
        try:
            if Path(logo_file).exists():
                with open(logo_file, 'rb') as f:
                    logo_data = base64.b64encode(f.read()).decode('utf-8')
                return f"data:image/jpeg;base64,{logo_data}"
        except Exception as e:
            print(f"⚠ Warning: Could not load logo: {e}")
        return None

    def generate_html(self):
        """Generate HTML version of the RFQ"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RFQ - {self.data['product']['name']} Board Game</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #f5f5f5;
        }}

        .container {{
            background: white;
            padding: 50px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}

        .header {{
            border-bottom: 4px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .header-content {{
            flex: 1;
        }}

        .header-logo {{
            max-width: 150px;
            max-height: 100px;
            object-fit: contain;
            margin-left: 30px;
        }}

        h1 {{
            color: #2c3e50;
            font-size: 28px;
            margin-bottom: 10px;
        }}

        .rfq-number {{
            color: #7f8c8d;
            font-size: 14px;
        }}

        .date {{
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 5px;
        }}

        h2 {{
            color: #34495e;
            font-size: 20px;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #ecf0f1;
        }}

        h3 {{
            color: #2c3e50;
            font-size: 16px;
            margin-top: 20px;
            margin-bottom: 10px;
        }}

        .info-section {{
            background: #f8f9fa;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 10px;
            margin: 10px 0;
        }}

        .info-label {{
            font-weight: 600;
            color: #555;
        }}

        .info-value {{
            color: #333;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}

        th {{
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }}

        tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        .component-card {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 20px;
            margin: 15px 0;
        }}

        .component-title {{
            font-weight: 600;
            color: #2c3e50;
            font-size: 18px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}

        .component-icon {{
            width: 8px;
            height: 8px;
            background: #3498db;
            border-radius: 50%;
            margin-right: 10px;
        }}

        .spec-list {{
            list-style: none;
            padding: 0;
        }}

        .spec-item {{
            padding: 8px 0;
            border-bottom: 1px dashed #ecf0f1;
        }}

        .spec-item:last-child {{
            border-bottom: none;
        }}

        .spec-name {{
            display: inline-block;
            min-width: 180px;
            font-weight: 500;
            color: #555;
        }}

        .spec-value {{
            color: #2c3e50;
        }}

        .important-note {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            margin: 20px 0;
        }}

        .legal-note {{
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px 20px;
            margin: 20px 0;
            font-size: 14px;
        }}

        .quality-list {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
        }}

        .quality-list ul {{
            margin-left: 20px;
            margin-top: 10px;
        }}

        .quality-list li {{
            margin: 8px 0;
        }}

        .moq-table {{
            background: white;
            margin: 20px 0;
        }}

        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>REQUEST FOR QUOTATION</h1>
                <div class="rfq-number">RFQ Number: BABI-{datetime.now().strftime('%Y%m%d')}-001</div>
                <div class="date">Date: {self.date}</div>
            </div>
            {f'<img src="{self.logo_base64}" alt="Babipoly Logo" class="header-logo">' if self.logo_base64 else ''}
        </div>

        <div class="info-section">
            <h2>Product Information</h2>
            <div class="info-grid">
                <div class="info-label">Product Name:</div>
                <div class="info-value"><strong>{self.data['product']['name']}</strong></div>

                <div class="info-label">Product Type:</div>
                <div class="info-value">{self.data['product']['type']}</div>

                <div class="info-label">Language:</div>
                <div class="info-value">{self.data['product']['language']}</div>

                <div class="info-label">Theme:</div>
                <div class="info-value">{self.data['product']['theme']}</div>

                <div class="info-label">Number of Players:</div>
                <div class="info-value">{self.data['product']['players']}</div>

                <div class="info-label">Target Age:</div>
                <div class="info-value">{self.data['product']['target_age']}</div>
            </div>
        </div>

        <div class="important-note">
            <strong>Note:</strong> {self.data['product']['artwork_status']}
            <br><strong>Purpose:</strong> {self.data['product']['rfq_purpose']}
        </div>

        <h2>Component Specifications</h2>
"""

        # Game Board
        board = self.data['components']['game_board']
        html += f"""
        <div class="component-card">
            <div class="component-title">
                <div class="component-icon"></div>
                1. Game Board
            </div>
            <ul class="spec-list">
                <li class="spec-item">
                    <span class="spec-name">Open Size:</span>
                    <span class="spec-value">{board['open_size_mm']} mm</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Folded Size:</span>
                    <span class="spec-value">{board['folded_size_mm']} mm</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Fold Type:</span>
                    <span class="spec-value">{board['fold_type']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Corners:</span>
                    <span class="spec-value">{board['corners']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Core Material:</span>
                    <span class="spec-value">{board['core_material']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Surface Paper:</span>
                    <span class="spec-value">{board['surface_paper']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Finish:</span>
                    <span class="spec-value">{board['finish']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Printing:</span>
                    <span class="spec-value">{board['printing']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Backside Printed:</span>
                    <span class="spec-value">{board['backside_printed']}</span>
                </li>
            </ul>
        </div>
"""

        # Cards
        cards = self.data['components']['cards']
        html += f"""
        <div class="component-card">
            <div class="component-title">
                <div class="component-icon"></div>
                2. Playing Cards (Total: {cards['total_quantity']} cards)
            </div>
            <ul class="spec-list">
                <li class="spec-item">
                    <span class="spec-name">Chance Cards:</span>
                    <span class="spec-value">{cards['types']['chance_cards']} cards</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Community Cards:</span>
                    <span class="spec-value">{cards['types']['community_cards']} cards</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Property Cards:</span>
                    <span class="spec-value">{cards['types']['property_cards']} cards</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Card Size:</span>
                    <span class="spec-value">{cards['size_mm']} mm</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Paper:</span>
                    <span class="spec-value">{cards['paper']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Finish:</span>
                    <span class="spec-value">{cards['finish']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Corners:</span>
                    <span class="spec-value">{cards['corners']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Printing:</span>
                    <span class="spec-value">{cards['printing']}</span>
                </li>
            </ul>
        </div>
"""

        # Paper Money
        money = self.data['components']['paper_money']
        html += f"""
        <div class="component-card">
            <div class="component-title">
                <div class="component-icon"></div>
                3. Paper Money (Total: {money['total_bills']} bills)
            </div>
            <table>
                <tr>
                    <th>Denomination</th>
                    <th>Quantity</th>
                </tr>
"""
        for denom, qty in money['denominations'].items():
            html += f"""
                <tr>
                    <td>{denom} F</td>
                    <td>{qty} bills</td>
                </tr>
"""
        html += f"""
            </table>
            <ul class="spec-list">
                <li class="spec-item">
                    <span class="spec-name">Bill Size:</span>
                    <span class="spec-value">{money['size_mm']} mm</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Paper:</span>
                    <span class="spec-value">{money['paper']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Printing:</span>
                    <span class="spec-value">{money['printing']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Note:</span>
                    <span class="spec-value">Monochrome printed on colored paper</span>
                </li>
            </ul>
        </div>
"""

        # Houses and Hotels
        buildings = self.data['components']['plastic_houses_hotels']
        html += f"""
        <div class="component-card">
            <div class="component-title">
                <div class="component-icon"></div>
                4. Houses & Hotels
            </div>
            <ul class="spec-list">
                <li class="spec-item">
                    <span class="spec-name">Green Houses:</span>
                    <span class="spec-value">{buildings['green_houses']} pieces</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Red Hotels:</span>
                    <span class="spec-value">{buildings['red_hotels']} pieces</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Material:</span>
                    <span class="spec-value">{buildings['material']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Manufacturing:</span>
                    <span class="spec-value">{buildings['manufacturing']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Size Reference:</span>
                    <span class="spec-value">{buildings['size_reference']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Note:</span>
                    <span class="spec-value">{buildings['note']}</span>
                </li>
            </ul>
        </div>
"""

        # Player Tokens
        tokens = self.data['components']['player_tokens']
        html += f"""
        <div class="component-card">
            <div class="component-title">
                <div class="component-icon"></div>
                5. Player Tokens
            </div>
            <ul class="spec-list">
                <li class="spec-item">
                    <span class="spec-name">Type:</span>
                    <span class="spec-value">{tokens['type']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Quantity:</span>
                    <span class="spec-value">{tokens['quantity']} pieces</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Material:</span>
                    <span class="spec-value">{tokens['material']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Manufacturing:</span>
                    <span class="spec-value">{tokens['manufacturing']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Size:</span>
                    <span class="spec-value">{tokens['size_mm']} mm</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Colors:</span>
                    <span class="spec-value">{', '.join(tokens['colors'])}</span>
                </li>
            </ul>
        </div>
"""

        # Dice
        dice = self.data['components']['dice']
        html += f"""
        <div class="component-card">
            <div class="component-title">
                <div class="component-icon"></div>
                6. Dice
            </div>
            <ul class="spec-list">
                <li class="spec-item">
                    <span class="spec-name">Quantity:</span>
                    <span class="spec-value">{dice['quantity']} dice</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Size:</span>
                    <span class="spec-value">{dice['size_mm']} mm</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Material:</span>
                    <span class="spec-value">{dice['material']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Color:</span>
                    <span class="spec-value">{dice['color']}</span>
                </li>
            </ul>
        </div>
"""

        # Instruction Booklet
        booklet = self.data['components']['instruction_booklet']
        html += f"""
        <div class="component-card">
            <div class="component-title">
                <div class="component-icon"></div>
                7. Instruction Booklet
            </div>
            <ul class="spec-list">
                <li class="spec-item">
                    <span class="spec-name">Pages:</span>
                    <span class="spec-value">{booklet['pages']} pages</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Size:</span>
                    <span class="spec-value">{booklet['size']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Paper:</span>
                    <span class="spec-value">{booklet['paper']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Printing:</span>
                    <span class="spec-value">{booklet['printing']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Binding:</span>
                    <span class="spec-value">{booklet['binding']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Finish:</span>
                    <span class="spec-value">{booklet['finish']}</span>
                </li>
            </ul>
        </div>
"""

        # Packaging
        pkg = self.data['components']['packaging']
        html += f"""
        <div class="component-card">
            <div class="component-title">
                <div class="component-icon"></div>
                8. Packaging
            </div>
            <ul class="spec-list">
                <li class="spec-item">
                    <span class="spec-name">Box Type:</span>
                    <span class="spec-value">{pkg['box_type']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Box Size:</span>
                    <span class="spec-value">{pkg['box_size_mm']} mm</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Material:</span>
                    <span class="spec-value">{pkg['material']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Finish:</span>
                    <span class="spec-value">{pkg['finish']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Insert:</span>
                    <span class="spec-value">{pkg['insert']}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Shrink Wrapped:</span>
                    <span class="spec-value">{"Yes" if pkg['shrink_wrapped'] else "No"}</span>
                </li>
                <li class="spec-item">
                    <span class="spec-name">Barcode Space:</span>
                    <span class="spec-value">{"Required" if pkg['barcode_space_required'] else "Not required"}</span>
                </li>
            </ul>
        </div>
"""

        # Quotation Request
        html += """
        <h2>Quotation Requirements</h2>
        <div class="moq-table">
            <h3>Please provide pricing for the following MOQ levels:</h3>
            <table>
                <tr>
                    <th>MOQ (Minimum Order Quantity)</th>
                </tr>
"""
        for moq in self.data['quotation_request']['moq_options']:
            html += f"""
                <tr>
                    <td><strong>{moq:,} units</strong></td>
                </tr>
"""
        html += """
            </table>
        </div>

        <h3>Required Information for Each MOQ:</h3>
        <table>
            <tr>
                <th>Information Type</th>
                <th>Details</th>
            </tr>
"""
        for info in self.data['quotation_request']['required_information']:
            html += f"""
            <tr>
                <td>{info}</td>
                <td style="color: #7f8c8d;">To be provided by manufacturer</td>
            </tr>
"""
        html += """
        </table>

        <div class="quality-list">
            <h3>Quality Requirements</h3>
            <ul>
"""
        for req in self.data['quality_requirements']:
            html += f"                <li>{req}</li>\n"

        html += f"""
            </ul>
        </div>

        <div class="legal-note">
            <strong>Legal Notice:</strong> {self.data['legal_note']}
        </div>

        <div class="footer">
            <p>This RFQ is generated for quotation purposes only.</p>
            <p>All specifications are subject to final artwork approval.</p>
            <p>Generated on {self.date}</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def generate_text(self):
        """Generate plain text version of the RFQ"""
        text = f"""
{'='*80}
                    REQUEST FOR QUOTATION
{'='*80}

RFQ Number: BABI-{datetime.now().strftime('%Y%m%d')}-001
Date: {self.date}

{'='*80}
PRODUCT INFORMATION
{'='*80}

Product Name:        {self.data['product']['name']}
Product Type:        {self.data['product']['type']}
Language:            {self.data['product']['language']}
Theme:               {self.data['product']['theme']}
Number of Players:   {self.data['product']['players']}
Target Age:          {self.data['product']['target_age']}

IMPORTANT NOTE:
{self.data['product']['artwork_status']}
Purpose: {self.data['product']['rfq_purpose']}

{'='*80}
COMPONENT SPECIFICATIONS
{'='*80}

1. GAME BOARD
{'-'*80}
"""
        board = self.data['components']['game_board']
        for key, value in board.items():
            text += f"   {key.replace('_', ' ').title():.<30} {value}\n"

        text += f"\n2. PLAYING CARDS (Total: {self.data['components']['cards']['total_quantity']} cards)\n"
        text += f"{'-'*80}\n"
        cards = self.data['components']['cards']
        text += f"   Types:\n"
        for card_type, qty in cards['types'].items():
            text += f"      - {card_type.replace('_', ' ').title()}: {qty} cards\n"
        text += f"\n   Specifications:\n"
        for key, value in cards.items():
            if key != 'types' and key != 'total_quantity':
                text += f"   {key.replace('_', ' ').title():.<30} {value}\n"

        text += f"\n3. PAPER MONEY (Total: {self.data['components']['paper_money']['total_bills']} bills)\n"
        text += f"{'-'*80}\n"
        money = self.data['components']['paper_money']
        text += "   Denominations:\n"
        for denom, qty in money['denominations'].items():
            text += f"      - {denom} F: {qty} bills\n"
        text += "\n   Specifications:\n"
        for key, value in money.items():
            if key not in ['denominations', 'total_bills']:
                text += f"   {key.replace('_', ' ').title():.<30} {value}\n"
        text += f"   Note:......................... Monochrome printed on colored paper\n"

        text += "\n4. HOUSES & HOTELS\n"
        text += f"{'-'*80}\n"
        buildings = self.data['components']['plastic_houses_hotels']
        for key, value in buildings.items():
            text += f"   {key.replace('_', ' ').title():.<30} {value}\n"

        text += "\n5. PLAYER TOKENS\n"
        text += f"{'-'*80}\n"
        tokens = self.data['components']['player_tokens']
        for key, value in tokens.items():
            if key == 'colors':
                text += f"   Colors: {', '.join(value)}\n"
            elif key == 'mold':
                continue  # Skip mold requirements
            else:
                text += f"   {key.replace('_', ' ').title():.<30} {value}\n"

        text += "\n6. DICE\n"
        text += f"{'-'*80}\n"
        dice = self.data['components']['dice']
        for key, value in dice.items():
            text += f"   {key.replace('_', ' ').title():.<30} {value}\n"

        text += "\n7. INSTRUCTION BOOKLET\n"
        text += f"{'-'*80}\n"
        booklet = self.data['components']['instruction_booklet']
        for key, value in booklet.items():
            text += f"   {key.replace('_', ' ').title():.<30} {value}\n"

        text += "\n8. PACKAGING\n"
        text += f"{'-'*80}\n"
        pkg = self.data['components']['packaging']
        for key, value in pkg.items():
            text += f"   {key.replace('_', ' ').title():.<30} {value}\n"

        text += f"\n{'='*80}\n"
        text += "QUOTATION REQUIREMENTS\n"
        text += f"{'='*80}\n\n"
        text += "Please provide pricing for the following MOQ levels:\n"
        for moq in self.data['quotation_request']['moq_options']:
            text += f"   - {moq:,} units\n"

        text += "\nRequired Information for Each MOQ:\n"
        for info in self.data['quotation_request']['required_information']:
            text += f"   • {info}\n"

        text += f"\n{'='*80}\n"
        text += "QUALITY REQUIREMENTS\n"
        text += f"{'='*80}\n"
        for req in self.data['quality_requirements']:
            text += f"   ✓ {req}\n"

        text += f"\n{'='*80}\n"
        text += "LEGAL NOTICE\n"
        text += f"{'='*80}\n"
        text += f"{self.data['legal_note']}\n"

        text += f"\n{'='*80}\n"
        text += f"Generated on {self.date}\n"
        text += f"{'='*80}\n"

        return text

    def save_html(self, filename='rfq_babipoly.html'):
        """Save HTML version to file"""
        html_content = self.generate_html()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✓ HTML RFQ saved to: {filename}")
        return filename

    def save_text(self, filename='rfq_babipoly.txt'):
        """Save text version to file"""
        text_content = self.generate_text()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text_content)
        print(f"✓ Text RFQ saved to: {filename}")
        return filename

    def save_pdf(self, filename='rfq_babipoly.pdf'):
        """Save PDF version using weasyprint"""
        try:
            from weasyprint import HTML
            html_content = self.generate_html()
            HTML(string=html_content).write_pdf(filename)
            print(f"✓ PDF RFQ saved to: {filename}")
            return filename
        except ImportError:
            print("⚠ PDF generation requires weasyprint. Install with: pip install weasyprint")
            print("  Alternatively, open the HTML file in a browser and print to PDF.")
            return None


def main():
    """Main function to generate RFQ documents"""
    print("\n" + "="*60)
    print("  BABIPOLY RFQ GENERATOR")
    print("="*60 + "\n")

    # Check if rfq.json exists
    if not Path('rfq.json').exists():
        print("❌ Error: rfq.json file not found!")
        print("   Please ensure rfq.json is in the current directory.")
        return

    # Generate RFQ
    generator = RFQGenerator('rfq.json')

    # Save in multiple formats
    print("Generating RFQ documents...\n")

    generator.save_html()
    generator.save_text()
    generator.save_pdf()

    print("\n" + "="*60)
    print("✓ RFQ Generation Complete!")
    print("="*60)
    print("\nYou can now:")
    print("  1. Open rfq_babipoly.html in your browser")
    print("  2. View rfq_babipoly.txt in any text editor")
    print("  3. Email rfq_babipoly.pdf to manufacturers")
    print("\n")


if __name__ == '__main__':
    main()
