import requests
from bs4 import BeautifulSoup
import csv
import re

# API URL and query parameters
url = "https://jacker.triplecrownsports.com/Tournament/GetRegistrations"
params = {
    "id": "10570",
    "sortBy": "TeamName",
    "_": "1746464943543"
}

# ✅ Your cookies
cookies = {
    ".AspNet.SharedCookie": "CfDJ8AlTajdgkWNJitwAPRoQPA_X30-RVHdiul293j6Yunv2_kMyE1-FC08Sjb3XLwS53O97AP1N2z6YCYkaljwwBgO_dZaWS216PGI5jnuZ_iizAGT1jAgy9kWypnlECnawhgp68mo4UpgEuAyUYlkM2_MStWW2UuiXYoNYZBry-u9RieMbs1J9x35Opt1FdURWywyqLKScHO0Dv_SshKSVmFE4RSUaZ3UUwvX3yGvGP5u1kgMrBO2e1f6lylQ-SvSZiGAwlhmnHJZmfDCQjQ5vb3wtkXV2ssFB_2KdDZrBSWTGnMUzxQoKISViTr8CT7SGhiiN5ZrrAoUVFMoK4MdwlhPfpogIs6w7HW56DkC_eG4wIsS3iwsKDYA3ALe8IcwuabuewMDyXU69-ZVaMdXDECTzM7yPK724Q0FE0a6fUJ6L1BO3aO2D1GkjaDNIKnQEDuQD-LQkjaKvyOfHFVeYCcOu_la2lPwHNgdOqB4TqzQ8",
    ".AspNetCore.Session": "CfDJ8AlTajdgkWNJitwAPRoQPA8m88xSlbr/bxP0GdcUkVI8QknuvVoRDGb4iSkD0e27ohE5ead4V9AUOYxwbkX6PMpOVBb9xVK7fsSeXenqDJFRAdneHVjSNtF9FnEn+UiF4q7JL52R8JzPM8XF6t7MvBNSHt3QMARO7VSeU02wb28S",
    "ARRAffinity": "79fc8c9d059d1f275dfaee94d0e3cee6a990a75a368124e8a7c56bb6fe584f82",
    "ARRAffinitySameSite": "79fc8c9d059d1f275dfaee94d0e3cee6a990a75a368124e8a7c56bb6fe584f82",
    ".AspNetCore.Antiforgery.qKMI6Lrj50Q": "CfDJ8AlTajdgkWNJitwAPRoQPA8eT8XHVS2yQDXMUu-P7hpVkkdq92-STaBBrPUbEF52XU2oq51wdKYPt7cGfgI-E8HNFWtUmJFnOGknb_VC0Md16VSDwlPsSJ_mycr9LQ8UAJLcSrXYIn0Y9nColxMJ-D4"
}

# Headers to simulate a browser request
headers = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest"
}

def extract_team_info(raw_team):
    """Extract 'Team Name' and 'Team ID' from string like 'Name (123456)'"""
    match = re.match(r"^(.*)\((\d+)\)$", raw_team)
    if match:
        return match.group(1).strip(), match.group(2)
    return raw_team.strip(), ""


def parse_section(soup, section_id, status, is_deleted=False):
    """Extract rows from Confirmed, Pending, or Deleted section"""
    section = soup.find("div", id=section_id)
    table = section.find("table") if section else None
    data = []

    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if not cols or len(cols) < 6:
                continue

            reg_number = cols[1].text.strip() if is_deleted else cols[0].text.strip()
            raw_team = cols[2].text.strip() if is_deleted else cols[1].text.strip()
            coach = cols[3].text.strip() if is_deleted else cols[2].text.strip()
            product = cols[4].text.strip() if is_deleted else cols[3].text.strip()
            division = cols[5].text.strip() if is_deleted else cols[4].text.strip()
            date = cols[6].text.strip() if is_deleted and len(cols) > 6 else ""

            team_name, team_id = extract_team_info(raw_team)

            data.append([
                reg_number, team_name, team_id, coach, product, division, date, status
            ])
    return data


# Make request and parse HTML
response = requests.get(url, params=params, cookies=cookies, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Parse all sections
confirmed = parse_section(soup, "ConfirmedRegistrations-10570", "Confirmed")
pending = parse_section(soup, "PendingRegistrations-10570", "Pending")
deleted = parse_section(soup, "DeletedRegistrations-10570", "Deleted", is_deleted=True)

# Combine and write CSV
all_data = confirmed + pending + deleted
with open("all_registrations.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        "Reg #", "Team Name", "Team ID", "Coach", "Product", "Division Sold", "Date", "Status"
    ])
    writer.writerows(all_data)

print("Combined data written to all_registrations.csv")