def _parse_page(soup: BeautifulSoup, page_url: str) -> list[dict]:
    records = []

    # 1. ახალ საიტზე პროდუქტის ბლოკები მოთავსებულია Div-ებში.
    # ვეძებთ ყველა იმ ელემენტს, რომელიც შეიცავს ლარის სიმბოლოს " ₾"
    price_tags = soup.find_all(string=lambda text: text and " ₾" in text)

    for price_tag in price_tags:
        # ვპოულობთ ფასის კონტეინერს
        price_container = price_tag.parent
        if not price_container:
            continue
            
        # ვეძებთ პროდუქტის მთავარ ბლოკს (მშობელ კონტეინერს)
        # ჩვეულებრივ ეს არის უახლოესი div, რომელიც აერთიანებს სახელს, ფასს და ღილაკს
        card = price_container.find_parent("div")
        if not card:
            continue

        # ── სახელი (Name) ──────────────────────────────────
        # ახალ საიტზე სახელი ხშირად არის პირდაპირი ტექსტი ან მარტივი ტეგი (h3/h4/p/span)
        # ვეძებთ ტექსტს, რომელიც შეიცავს ტირეს ბრენდის გამოსაყოფად (მაგ: "ტირტირი - სახის...")
        name_el = card.find(string=lambda text: text and " - " in text)
        if not name_el:
            # თუ ტირე არ არის, ავიღოთ ბლოკში არსებული პირველი გრძელი ტექსტი
            name_elements = [s.strip() for s in card.stripped_strings if len(s.strip()) > 5 and "₾" not in s]
            name = name_elements[0] if name_elements else None
        else:
            name = name_el.strip()

        if not name or len(name) < 2:
            continue

        # დუბლიკატების თავიდან ასაცილებლად (რადგან ერთი და იგივე div შეიძლება რამდენჯერმე დამუშავდეს)
        if any(r[COL_NAME] == name[:100] for r in records):
            continue

        # ── მიმდინარე ფასი (Current Price) ──────────────────
        price = parse_price(price_tag)
        if price is None:
            continue

        # ── ძველი ფასი (Old Price) ─────────────────────────
        # ახალ ვერსიაში ძველი ფასი ხშირად წერია მიმდინარე ფასის გვერდით ან ქვემოთ, ლარის ნიშნით (მაგ. 5.95₾)
        old_price = None
        # ვეძებთ ბლოკში ყველა ტექსტს, სადაც არის "₾", მაგრამ არ არის მიმდინარე ფასის ტექსტი
        all_prices = card.find_all(string=lambda text: text and "₾" in text)
        for p_str in all_prices:
            if " ₾" not in p_str: # ახალ ფასს აქვს გამოტოვებული ადგილი " ₾", ძველს კი მიწებებული "5.95₾"
                parsed_old = parse_price(p_str)
                if parsed_old and parsed_old > price:
                    old_price = parsed_old
                    break

        # ── ლინკი (URL) ─────────────────────────────────────
        # ვეძებთ პროდუქტის შიდა ბმულს, ახალ საიტზე ხშირად გამოიყენება /product/ ან /medicament/
        link_el = card.select_one("a[href*='product']") or card.select_one("a[href*='medicament']") or card.select_one("a[href]")
        href = link_el["href"] if link_el else page_url
        if href and not href.startswith("http"):
            href = "https://gpc.ge" + href

        brand    = extract_brand(name)
        subcat   = classify_subcategory(name)
        disc_pct = calc_discount_pct(old_price, price)

        records.append({
            COL_NAME:      name[:100],
            COL_PRICE:     price,
            COL_OLD_PRICE: old_price,
            COL_DISCOUNT:  disc_pct,
            COL_BRAND:     brand,
            COL_CATEGORY:  subcat,
            COL_SOURCE:    "GPC",
            COL_URL:       href,
            COL_NORM_KEY:  normalize_key(name),
            COL_UPDATED:   datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return records
