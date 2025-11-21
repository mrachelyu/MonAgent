import pandas as pd

def load_business_data(csv_path):
    df = pd.read_csv(csv_path)

    data = {
        "services": [],
        "about": None,
        "join_info": None,
        "pricing_summary": None,
        "testimonials": [],
        "links": [],
        "address": None,
        "phone": None,
        "email": None,
    }

    for _, row in df.iterrows():
        t = row["type"]

        # Services
        if t == "service":
            data["services"].append({
                "units": row["units"],
                "price": row["price"],
                "member_fee_month": row["member_fee_month"]
            })
            if not data["address"] and pd.notna(row["address"]):
                data["address"] = row["address"]
            if not data["phone"] and pd.notna(row["phone"]):
                data["phone"] = row["phone"]
            if not data["email"] and pd.notna(row["email"]):
                data["email"] = row["email"]

        # About
        elif t == "about":
            data["about"] = row["content"]

        # Membership / Joining
        elif t == "join_info":
            data["join_info"] = row["content"]

        # Pricing summary
        elif t == "pricing_summary":
            data["pricing_summary"] = row["content"]

        # Testimonials
        elif t == "testimonial":
            data["testimonials"].append(row["content"])

        # Links
        elif t == "link":
            data["links"].append({
                "text": row["link_text"],
                "url": row["link_url"]
            })

    return data
