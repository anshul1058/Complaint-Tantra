# Institutions CSV — Column Guide

For: the member collecting real AICTE college data.
One row = one campus. Public data only (AICTE approved-institution data + college websites).

## CSV header (copy-paste exactly)

```
permanent_id,institution_name,short_name,institute_type,constitution,category,programmes_offered,total_approved_intake,approval_status,address_line1,address_line2,city,district,state,pincode,latitude,longitude,aicte_region,trust_name,campus_name,affiliated_university,phone,mobile,email,website,principal_name,year_of_establishment,approval_valid_till,nba_accredited,naac_grade,hostel_available,gender_policy,source_url,notes
```

## Field guide

### Identity (AICTE official)

| Column | What to fill | Why it matters |
|---|---|---|
| `permanent_id` | AICTE Permanent ID. Leave blank if unknown (~25% missing is realistic) | Main key for matching/dedup |
| `institution_name` | Full name exactly as on the AICTE approval letter — **do not clean typos/abbreviations** | The fuzzy matcher is built for messy names |
| `short_name` | Local/common name ("VJTI", "COEP") | Complaints often use only this |
| `institute_type` | Govt / Govt-Aided / Self-Financed / Private University / Deemed University | Risk context |
| `constitution` | Trust / Society / Company / Pvt Ltd / Section 8 | Multi-campus grouping |
| `category` | Technical / Management / Pharmacy / Architecture / Hotel Mgmt / Applied Arts | Bureau routing |
| `programmes_offered` | Semicolon list, e.g. `BTech;MTech;MBA;MCA;Diploma` | Overlap + risk signals |
| `total_approved_intake` | Sum of approved seats (number) | Scale of institution |
| `approval_status` | Approved / Withheld / Closed | Hard filter |

### Location

| Column | What to fill |
|---|---|
| `address_line1`, `address_line2` | Full address |
| `city`, `district`, `state`, `pincode` | — |
| `latitude`, `longitude` | Optional but powers the dashboard heatmap |
| `aicte_region` | Regional office jurisdiction (North / South / East / West / Central / North-East) — map from state |

### Ownership (multi-campus grouping)

| Column | What to fill |
|---|---|
| `trust_name` | Trust/society running it — same trust across cities = sibling campuses |
| `campus_name` | Distinct campus label if the trust has several |
| `affiliated_university` | Affiliating university |

### Contact

| Column | What to fill |
|---|---|
| `phone`, `mobile`, `email`, `website` | Public contact data |
| `principal_name` | Public, from college site |

### History / quality

| Column | What to fill |
|---|---|
| `year_of_establishment` | — |
| `approval_valid_till` | AICTE approval validity date, ISO `YYYY-MM-DD` |
| `nba_accredited` | yes / no / valid-till-date |
| `naac_grade` | A++ / A+ / A / B++ / B+ / B / C if known, else blank |
| `hostel_available` | yes / no |
| `gender_policy` | co-ed / girls-only / boys-only |

### Audit

| Column | What to fill |
|---|---|
| `source_url` | Where the record came from (AICTE portal page, college site) |
| `notes` | Anything odd about the record |

## Rules

- **UTF-8 CSV**, comma-separated, header row exactly as above
- No merged cells; use blanks instead of "N/A" or "-"
- One row per campus. If a college offers 6 programmes, semicolon-join them — do NOT make 6 rows
- Target **500+ rows**, mix of states
- Keep real messiness (abbreviations, "Engg" vs "Engineering", missing IDs) — the matcher demo depends on it
- Public institutional data only. No personal student/staff data.

## Not in the CSV (computed in code)

`name_normalized`, `name_embedding`, `risk_index`, UUID `id`, `created_at` — the system derives these on ingest.
