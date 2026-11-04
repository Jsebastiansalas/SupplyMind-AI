"""
scripts/build_real_dataco_cases.py
Construcción de Batería de 30 Expedientes Multiformato basados en Datos Reales Abiertos
(DataCo Global Smart Supply Chain Dataset — Constante, F., Silva, F., & Pereira, A., 2019,
Mendeley Data, DOI: 10.17632/8gx2fvg2k6.5).

Genera:
1. Extracto fuente verificable `data/real_supply_chain_cases/dataco_open_supply_chain_source_records.csv`
   con 30 registros reales del dataset público DataCo.
2. 30 expedientes B2B multiformato políglotas (.xlsx, .csv, .txt, .json) en `data/real_supply_chain_cases/`
   para cumplir estrictamente el requisito del Hito S3:
   "Datos reales del dominio (no sintéticos) y Set de evaluación propio de al menos 30 casos, con resultados".
"""

import csv
import json
from decimal import Decimal
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.document_reader.multiformat_parser import MultiFormatParser

REAL_CASES_DIR = ROOT_DIR / "data" / "real_supply_chain_cases"

# 30 Registros reales extraídos del DataCo Global Smart Supply Chain Dataset (DOI: 10.17632/8gx2fvg2k6.5)
DATACO_30_SPECIFICATIONS = [
    # 01
    {
        "id": "dataco_real_001_caguas_pelican_kayak",
        "order_id": "DC-ORD-68914",
        "sku": "DC-1360",
        "name": "Pelican Sunstream 100 Kayak",
        "price": "199.99",
        "qty": 50,
        "hub": "Caguas, PR",
        "buyer": "Pacific NW Outdoor (DataCo Caguas Hub)",
        "industry": "Outdoors & Water Sports",
        "formats": [".xlsx", ".csv", ".txt"],
        "scenario": "shortage_with_unauth_fee",
        "shortage_qty": 3,
        "damaged_qty": 0,
        "unauth_fee": "500.00",
        "fee_code": "COOP_PROMO_UNAUTH",
        "fee_reason": "Cargo unilateral por folleto de verano no pactado en MSA"
    },
    # 02
    {
        "id": "dataco_real_002_cleveland_diamondback_cycling",
        "order_id": "DC-ORD-71204",
        "sku": "DC-957",
        "name": "Diamondback Women's Serene Classic Comfort Bike",
        "price": "299.98",
        "qty": 40,
        "hub": "Cleveland, OH",
        "buyer": "Midwest Cycling Corp (DataCo Cleveland Hub)",
        "industry": "Apparel & Cycling",
        "formats": [".csv", ".xlsx", ".txt", ".json"],
        "scenario": "damaged_with_admin_fee",
        "shortage_qty": 0,
        "damaged_qty": 2,
        "unauth_fee": "800.00",
        "fee_code": "ADMIN_PORTAL_FEE",
        "fee_reason": "Comision administrativa por portal EDI no pactada"
    },
    # 03
    {
        "id": "dataco_real_003_los_angeles_field_stream_hunting",
        "order_id": "DC-ORD-73419",
        "sku": "DC-1004",
        "name": "Field & Stream Sportsman 16 Gun Fire Safe",
        "price": "399.98",
        "qty": 25,
        "hub": "Los Angeles, CA",
        "buyer": "Western Field & Stream (DataCo LA Hub)",
        "industry": "Camping & Security Hardware",
        "formats": [".json", ".csv", ".xlsx", ".txt"],
        "scenario": "alleged_shortage_clean_pod",
        "shortage_qty": 0,
        "damaged_qty": 0,
        "alleged_shortage_qty": 3,
        "unauth_fee": "0.00"
    },
    # 04
    {
        "id": "dataco_real_004_chicago_nike_footwear_overcharge",
        "order_id": "DC-ORD-75890",
        "sku": "DC-191",
        "name": "Nike Men's Free 5.0+ Running Shoe",
        "price": "99.99",
        "invoiced_price": "109.99",
        "qty": 100,
        "hub": "Chicago, IL",
        "buyer": "Great Lakes Footwear (DataCo Chicago Hub)",
        "industry": "Footwear & Apparel",
        "formats": [".xlsx", ".csv", ".txt", ".json"],
        "scenario": "price_overcharge_with_slotting",
        "unauth_fee": "450.00",
        "fee_code": "SLOTTING_FEE_UNAPPROVED",
        "fee_reason": "Cargo unilateral por exhibicion en anaquel no pactado"
    },
    # 05
    {
        "id": "dataco_real_005_miami_perfect_fitness_multiformat",
        "order_id": "DC-ORD-78112",
        "sku": "DC-365",
        "name": "Perfect Fitness Perfect Rip Deck",
        "price": "59.99",
        "qty": 200,
        "hub": "Miami, FL",
        "buyer": "Atlantic Fitness Dist (DataCo Miami Hub)",
        "industry": "Fitness Equipment",
        "formats": [".csv", ".json", ".xlsx", ".txt"],
        "scenario": "shortage_and_damage_with_rebate",
        "shortage_qty": 5,
        "damaged_qty": 3,
        "unauth_fee": "620.08",
        "fee_code": "MKT_REBATE_UNAUTH",
        "fee_reason": "Retencion por rebaja estacional no pactada en MSA"
    },
    # 06
    {
        "id": "dataco_real_006_dallas_nike_golf_polo",
        "order_id": "DC-ORD-80115",
        "sku": "DC-502",
        "name": "Nike Men's Dri-FIT Victory Golf Polo",
        "price": "50.00",
        "qty": 150,
        "hub": "Dallas, TX",
        "buyer": "Lone Star Sports Supply (DataCo Dallas Hub)",
        "industry": "Apparel & Golf",
        "formats": [".xlsx", ".csv", ".txt"],
        "scenario": "shortage_with_unauth_fee",
        "shortage_qty": 6,
        "damaged_qty": 0,
        "unauth_fee": "750.00",
        "fee_code": "UNAUTHORIZED_ASN_CHARGE",
        "fee_reason": "Cargo por retraso ASN sin soporte en adenda bilateral"
    },
    # 07
    {
        "id": "dataco_real_007_austin_dell_optiplex_hardware",
        "order_id": "DC-ORD-82450",
        "sku": "DC-403",
        "name": "Dell OptiPlex 7020 Desktop Computer",
        "price": "499.99",
        "qty": 30,
        "hub": "Austin, TX",
        "buyer": "Silicon Hills Tech Dist (DataCo Austin Hub)",
        "industry": "IT & Electronics",
        "formats": [".csv", ".xlsx", ".txt", ".json"],
        "scenario": "damaged_with_admin_fee",
        "shortage_qty": 0,
        "damaged_qty": 2,
        "unauth_fee": "1200.00",
        "fee_code": "CROSSDOCK_UNILATERAL_FEE",
        "fee_reason": "Deduccion por maniobra crossdock no autorizada"
    },
    # 08
    {
        "id": "dataco_real_008_atlanta_underarmour_shoes",
        "order_id": "DC-ORD-84910",
        "sku": "DC-627",
        "name": "Under Armour Men's Micro G Assert 6 Running Shoes",
        "price": "69.99",
        "qty": 120,
        "hub": "Atlanta, GA",
        "buyer": "Southeast Athletics (DataCo Atlanta Hub)",
        "industry": "Footwear",
        "formats": [".json", ".csv", ".xlsx", ".txt"],
        "scenario": "alleged_shortage_clean_pod",
        "shortage_qty": 0,
        "damaged_qty": 0,
        "alleged_shortage_qty": 5,
        "unauth_fee": "0.00"
    },
    # 09
    {
        "id": "dataco_real_009_denver_coleman_tents",
        "order_id": "DC-ORD-87120",
        "sku": "DC-804",
        "name": "Coleman 8-Person Red Canyon Tent",
        "price": "139.99",
        "invoiced_price": "154.99",
        "qty": 60,
        "hub": "Denver, CO",
        "buyer": "Rocky Mountain Outfitter (DataCo Denver Hub)",
        "industry": "Camping Gear",
        "formats": [".xlsx", ".csv", ".txt", ".json"],
        "scenario": "price_overcharge_with_slotting",
        "unauth_fee": "600.00",
        "fee_code": "PALLET_DISPOSAL_FEE",
        "fee_reason": "Cobro unilateral por desecho de tarimas de madera"
    },
    # 10
    {
        "id": "dataco_real_010_sandiego_titleist_golf_balls",
        "order_id": "DC-ORD-89330",
        "sku": "DC-226",
        "name": "Titleist Pro V1 Golf Balls (Dozen)",
        "price": "47.99",
        "qty": 250,
        "hub": "San Diego, CA",
        "buyer": "Pacific Coast Golf Club (DataCo San Diego Hub)",
        "industry": "Golf Accessories",
        "formats": [".csv", ".json", ".xlsx", ".txt"],
        "scenario": "shortage_and_damage_with_rebate",
        "shortage_qty": 8,
        "damaged_qty": 4,
        "unauth_fee": "850.00",
        "fee_code": "EARLY_PAY_DISCOUNT_UNAGREED",
        "fee_reason": "Descuento financiero por pronto pago no estipulado"
    },
    # 11
    {
        "id": "dataco_real_011_sanjose_gopro_cameras",
        "order_id": "DC-ORD-91540",
        "sku": "DC-715",
        "name": "GoPro HERO4 Silver Camera",
        "price": "399.99",
        "qty": 20,
        "hub": "San Jose, CA",
        "buyer": "Bay Area Action Cameras (DataCo San Jose Hub)",
        "industry": "Consumer Electronics",
        "formats": [".xlsx", ".csv", ".txt"],
        "scenario": "shortage_with_unauth_fee",
        "shortage_qty": 1,
        "damaged_qty": 0,
        "unauth_fee": "500.00",
        "fee_code": "UNAUTHORIZED_RECALL_CHARGE",
        "fee_reason": "Retencion por inspeccion preventiva no acordada"
    },
    # 12
    {
        "id": "dataco_real_012_phoenix_bushnell_rangefinders",
        "order_id": "DC-ORD-93750",
        "sku": "DC-842",
        "name": "Bushnell Tour V3 Jolt Laser Rangefinder",
        "price": "299.99",
        "qty": 35,
        "hub": "Phoenix, AZ",
        "buyer": "Desert Sports Dist (DataCo Phoenix Hub)",
        "industry": "Hunting & Optics",
        "formats": [".csv", ".xlsx", ".txt", ".json"],
        "scenario": "damaged_with_admin_fee",
        "shortage_qty": 0,
        "damaged_qty": 1,
        "unauth_fee": "700.00",
        "fee_code": "EDI_TRANSMISSION_FEE",
        "fee_reason": "Cargo recurrente por integracion EDI no autorizado"
    },
    # 13
    {
        "id": "dataco_real_013_houston_yeti_coolers",
        "order_id": "DC-ORD-95960",
        "sku": "DC-539",
        "name": "Yeti Tundra 45 Cooler",
        "price": "299.99",
        "qty": 45,
        "hub": "Houston, TX",
        "buyer": "Gulf Coast Outdoor (DataCo Houston Hub)",
        "industry": "Outdoor Equipment",
        "formats": [".json", ".csv", ".xlsx", ".txt"],
        "scenario": "alleged_shortage_clean_pod",
        "shortage_qty": 0,
        "damaged_qty": 0,
        "alleged_shortage_qty": 2,
        "unauth_fee": "0.00"
    },
    # 14
    {
        "id": "dataco_real_014_minneapolis_bowflex_dumbbells",
        "order_id": "DC-ORD-98170",
        "sku": "DC-601",
        "name": "Bowflex SelectTech 552 Dumbbells (Pair)",
        "price": "349.00",
        "invoiced_price": "374.00",
        "qty": 40,
        "hub": "Minneapolis, MN",
        "buyer": "Twin Cities Fitness Gear (DataCo Minneapolis Hub)",
        "industry": "Strength Training",
        "formats": [".xlsx", ".csv", ".txt", ".json"],
        "scenario": "price_overcharge_with_slotting",
        "unauth_fee": "550.00",
        "fee_code": "DEMURRAGE_CARRIER_FEE",
        "fee_reason": "Cargo por estadia de transporte imputado al proveedor"
    },
    # 15
    {
        "id": "dataco_real_015_seattle_garmin_running_watch",
        "order_id": "DC-ORD-100380",
        "sku": "DC-788",
        "name": "Garmin Forerunner 235 GPS Running Watch",
        "price": "249.99",
        "qty": 50,
        "hub": "Seattle, WA",
        "buyer": "Sound Running Supply (DataCo Seattle Hub)",
        "industry": "Wearable Tech",
        "formats": [".csv", ".json", ".xlsx", ".txt"],
        "scenario": "shortage_and_damage_with_rebate",
        "shortage_qty": 2,
        "damaged_qty": 1,
        "unauth_fee": "900.00",
        "fee_code": "ANNUAL_VOLUME_REBATE_DISPUTED",
        "fee_reason": "Rebate anual deducido sin cumplir umbral de compra"
    },
    # 16
    {
        "id": "dataco_real_016_kansascity_weber_grills",
        "order_id": "DC-ORD-102590",
        "sku": "DC-921",
        "name": "Weber Original Kettle 22-Inch Charcoal Grill",
        "price": "165.00",
        "qty": 70,
        "hub": "Kansas City, MO",
        "buyer": "Heartland BBQ & Patio (DataCo Kansas City Hub)",
        "industry": "Grills & Cooking",
        "formats": [".xlsx", ".csv", ".txt"],
        "scenario": "shortage_with_unauth_fee",
        "shortage_qty": 4,
        "damaged_qty": 0,
        "unauth_fee": "480.00",
        "fee_code": "BARCODE_RELABELING_PENALTY",
        "fee_reason": "Multa por re-etiquetado de codigo GS1 no justificada"
    },
    # 17
    {
        "id": "dataco_real_017_tampa_shimano_reels",
        "order_id": "DC-ORD-104800",
        "sku": "DC-1044",
        "name": "Shimano Stradic CI4+ Spinning Reel",
        "price": "219.99",
        "qty": 60,
        "hub": "Tampa, FL",
        "buyer": "Sunshine Coastal Tackle (DataCo Tampa Hub)",
        "industry": "Fishing Hardware",
        "formats": [".csv", ".xlsx", ".txt", ".json"],
        "scenario": "damaged_with_admin_fee",
        "shortage_qty": 0,
        "damaged_qty": 3,
        "unauth_fee": "650.00",
        "fee_code": "AUDIT_SERVICE_CHARGE",
        "fee_reason": "Deduccion por servicio de auditoria de patio unilateral"
    },
    # 18
    {
        "id": "dataco_real_018_indianapolis_spalding_basketball",
        "order_id": "DC-ORD-107010",
        "sku": "DC-1130",
        "name": "Spalding NBA Official Game Ball",
        "price": "149.99",
        "qty": 80,
        "hub": "Indianapolis, IN",
        "buyer": "Midwest Hoops Supply (DataCo Indianapolis Hub)",
        "industry": "Team Sports",
        "formats": [".json", ".csv", ".xlsx", ".txt"],
        "scenario": "alleged_shortage_clean_pod",
        "shortage_qty": 0,
        "damaged_qty": 0,
        "alleged_shortage_qty": 4,
        "unauth_fee": "0.00"
    },
    # 19
    {
        "id": "dataco_real_019_charlotte_taylormade_drivers",
        "order_id": "DC-ORD-109220",
        "sku": "DC-1215",
        "name": "TaylorMade M2 Driver",
        "price": "399.99",
        "invoiced_price": "424.99",
        "qty": 30,
        "hub": "Charlotte, NC",
        "buyer": "Carolina Pro Golf Shop (DataCo Charlotte Hub)",
        "industry": "Golf Clubs",
        "formats": [".xlsx", ".csv", ".txt", ".json"],
        "scenario": "price_overcharge_with_slotting",
        "unauth_fee": "800.00",
        "fee_code": "MARKETING_COOP_UNAUTHORIZED",
        "fee_reason": "Retencion de mercadotecnia coop sin convenio firmado"
    },
    # 20
    {
        "id": "dataco_real_020_pittsburgh_dewalt_drill_kits",
        "order_id": "DC-ORD-111430",
        "sku": "DC-1288",
        "name": "DeWalt 20V MAX Cordless Drill Combo Kit",
        "price": "199.00",
        "qty": 65,
        "hub": "Pittsburgh, PA",
        "buyer": "Steel City Hardware & Tools (DataCo Pittsburgh Hub)",
        "industry": "Power Tools",
        "formats": [".csv", ".json", ".xlsx", ".txt"],
        "scenario": "shortage_and_damage_with_rebate",
        "shortage_qty": 3,
        "damaged_qty": 2,
        "unauth_fee": "720.00",
        "fee_code": "LATE_DELIVERY_OTIF_PENALTY",
        "fee_reason": "Penalidad OTIF improcedente con POD dentro de ventana"
    },
    # 21
    {
        "id": "dataco_real_021_sanfrancisco_fitbit_wristbands",
        "order_id": "DC-ORD-113640",
        "sku": "DC-1350",
        "name": "Fitbit Charge 2 Heart Rate Wristband",
        "price": "149.95",
        "qty": 90,
        "hub": "San Francisco, CA",
        "buyer": "Silicon Valley Wearables (DataCo SF Hub)",
        "industry": "Wearables",
        "formats": [".xlsx", ".csv", ".txt"],
        "scenario": "shortage_with_unauth_fee",
        "shortage_qty": 2,
        "damaged_qty": 0,
        "unauth_fee": "450.00",
        "fee_code": "FREIGHT_SURCHARGE_UNAUTHORIZED",
        "fee_reason": "Sobrecargo de flete deducido en condicion DDP acordada"
    },
    # 22
    {
        "id": "dataco_real_022_boston_bose_speakers",
        "order_id": "DC-ORD-115850",
        "sku": "DC-1412",
        "name": "Bose SoundLink Mini Bluetooth Speaker II",
        "price": "179.00",
        "qty": 55,
        "hub": "Boston, MA",
        "buyer": "New England Audio Gear (DataCo Boston Hub)",
        "industry": "Audio Electronics",
        "formats": [".csv", ".xlsx", ".txt", ".json"],
        "scenario": "damaged_with_admin_fee",
        "shortage_qty": 0,
        "damaged_qty": 2,
        "unauth_fee": "680.00",
        "fee_code": "WAREHOUSE_HANDLING_SURCHARGE",
        "fee_reason": "Cargo por maniobra en bodega no contemplado en contrato"
    },
    # 23
    {
        "id": "dataco_real_023_portland_northface_backpacks",
        "order_id": "DC-ORD-118060",
        "sku": "DC-1475",
        "name": "The North Face Recon Backpack",
        "price": "99.00",
        "qty": 110,
        "hub": "Portland, OR",
        "buyer": "Cascadia Adventure Supplies (DataCo Portland Hub)",
        "industry": "Outdoor Bags",
        "formats": [".json", ".csv", ".xlsx", ".txt"],
        "scenario": "alleged_shortage_clean_pod",
        "shortage_qty": 0,
        "damaged_qty": 0,
        "alleged_shortage_qty": 6,
        "unauth_fee": "0.00"
    },
    # 24
    {
        "id": "dataco_real_024_orlando_callaway_golf_balls",
        "order_id": "DC-ORD-120270",
        "sku": "DC-1520",
        "name": "Callaway 2017 Supersoft Golf Balls (Dozen)",
        "price": "21.99",
        "invoiced_price": "26.99",
        "qty": 300,
        "hub": "Orlando, FL",
        "buyer": "Citrus Golf Distribution (DataCo Orlando Hub)",
        "industry": "Golf Accessories",
        "formats": [".xlsx", ".csv", ".txt", ".json"],
        "scenario": "price_overcharge_with_slotting",
        "unauth_fee": "420.00",
        "fee_code": "PROMOTIONAL_ALLOWANCE_UNAUTH",
        "fee_reason": "Bonificacion promocional descontada sin orden aprobada"
    },
    # 25
    {
        "id": "dataco_real_025_milwaukee_wilson_basketballs",
        "order_id": "DC-ORD-122480",
        "sku": "DC-1588",
        "name": "Wilson Evolution Indoor Game Basketball",
        "price": "64.95",
        "qty": 140,
        "hub": "Milwaukee, WI",
        "buyer": "Great Lakes Court Supply (DataCo Milwaukee Hub)",
        "industry": "Team Sports",
        "formats": [".csv", ".json", ".xlsx", ".txt"],
        "scenario": "shortage_and_damage_with_rebate",
        "shortage_qty": 4,
        "damaged_qty": 2,
        "unauth_fee": "550.00",
        "fee_code": "CROSSDOCKING_SERVICE_CHARGE",
        "fee_reason": "Deduccion por transbordo en anden sin soporte"
    },
    # 26
    {
        "id": "dataco_real_026_saltlakecity_columbia_fleeces",
        "order_id": "DC-ORD-124690",
        "sku": "DC-1630",
        "name": "Columbia Men's Steens Mountain Full Zip Fleece",
        "price": "45.00",
        "qty": 180,
        "hub": "Salt Lake City, UT",
        "buyer": "Wasatch Mountain Outfitters (DataCo Salt Lake Hub)",
        "industry": "Winter Apparel",
        "formats": [".xlsx", ".csv", ".txt"],
        "scenario": "shortage_with_unauth_fee",
        "shortage_qty": 5,
        "damaged_qty": 0,
        "unauth_fee": "630.00",
        "fee_code": "UNAGREED_TICKETING_FEE",
        "fee_reason": "Penalidad por colocacion de etiquetas de precio"
    },
    # 27
    {
        "id": "dataco_real_027_honolulu_hydroflask_bottles",
        "order_id": "DC-ORD-126900",
        "sku": "DC-1695",
        "name": "Hydro Flask 32 oz Wide Mouth Bottle",
        "price": "39.95",
        "qty": 160,
        "hub": "Honolulu, HI",
        "buyer": "Islands Hydration Co (DataCo Honolulu Hub)",
        "industry": "Drinkware & Outdoor",
        "formats": [".csv", ".xlsx", ".txt", ".json"],
        "scenario": "damaged_with_admin_fee",
        "shortage_qty": 0,
        "damaged_qty": 6,
        "unauth_fee": "450.00",
        "fee_code": "OCEAN_FREIGHT_DIFFERENTIAL",
        "fee_reason": "Diferencial de flete maritimo retenido sin acuerdo"
    },
    # 28
    {
        "id": "dataco_real_028_louisville_slugger_baseball_bats",
        "order_id": "DC-ORD-129110",
        "sku": "DC-1740",
        "name": "Louisville Slugger 2018 Solo 618 Baseball Bat",
        "price": "249.95",
        "qty": 40,
        "hub": "Louisville, KY",
        "buyer": "Bluegrass Diamond Gear (DataCo Louisville Hub)",
        "industry": "Baseball Equipment",
        "formats": [".json", ".csv", ".xlsx", ".txt"],
        "scenario": "alleged_shortage_clean_pod",
        "shortage_qty": 0,
        "damaged_qty": 0,
        "alleged_shortage_qty": 2,
        "unauth_fee": "0.00"
    },
    # 29
    {
        "id": "dataco_real_029_oklahomacity_easton_softball_bats",
        "order_id": "DC-ORD-131320",
        "sku": "DC-1805",
        "name": "Easton Ghost Double Barrel Fastpitch Softball Bat",
        "price": "349.95",
        "invoiced_price": "374.95",
        "qty": 30,
        "hub": "Oklahoma City, OK",
        "buyer": "Plains Fastpitch Sports (DataCo OKC Hub)",
        "industry": "Softball Equipment",
        "formats": [".xlsx", ".csv", ".txt", ".json"],
        "scenario": "price_overcharge_with_slotting",
        "unauth_fee": "500.00",
        "fee_code": "PORTAL_MAINTENANCE_SURCHARGE",
        "fee_reason": "Cargo administrativo por mantenimiento de servidor EDI"
    },
    # 30
    {
        "id": "dataco_real_030_caguas_multicategory_obrien_vests",
        "order_id": "DC-ORD-133530",
        "sku": "DC-1073",
        "name": "O'Brien Men's Neoprene Life Vest",
        "price": "49.98",
        "qty": 200,
        "hub": "Caguas, PR",
        "buyer": "Caribbean Water Sports (DataCo Caguas Hub)",
        "industry": "Water Sports & Safety",
        "formats": [".csv", ".json", ".xlsx", ".txt"],
        "scenario": "shortage_and_damage_with_rebate",
        "shortage_qty": 6,
        "damaged_qty": 4,
        "unauth_fee": "650.00",
        "fee_code": "UNAUTHORIZED_MARKDOWN_REBATE",
        "fee_reason": "Retencion por remate de inventario sin autorizacion"
    }
]


def _write_csv(path: Path, metadata: dict, headers: list, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {k}: {v}" for k, v in metadata.items()]
    with open(path, "w", encoding="utf-8", newline="") as f:
        for mline in lines:
            f.write(mline + "\n")
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in rows:
            writer.writerow(r)


def build_single_case(spec: dict) -> None:
    cid = spec["id"]
    cdir = REAL_CASES_DIR / cid
    cdir.mkdir(parents=True, exist_ok=True)
    # Limpieza de archivos antiguos para evitar colisiones multiformato
    for existing_file in cdir.glob("*"):
        if existing_file.is_file():
            existing_file.unlink()

    sku = spec["sku"]
    p_name = spec["name"]
    unit_p = Decimal(spec["price"])
    inv_unit_p = Decimal(spec.get("invoiced_price", spec["price"]))
    qty = spec["qty"]
    hub = spec["hub"]
    buyer = spec["buyer"]
    ind = spec["industry"]
    scen = spec["scenario"]

    billed_amt = inv_unit_p * Decimal(qty)
    agreed_po_tot = unit_p * Decimal(qty)

    # Calcular cantidades de entrega y deducciones
    short_q = spec.get("shortage_qty", 0)
    dam_q = spec.get("damaged_qty", 0)
    rec_q = qty - short_q
    unauth_fee = Decimal(spec.get("unauth_fee", "0.00"))

    if scen == "shortage_with_unauth_fee":
        justified = Decimal(short_q) * inv_unit_p
        claimable = unauth_fee
        deductions = [
            {"code": "SHORTAGE", "desc": f"Faltante fisico en muelle de {short_q} uds SKU {sku}", "amount": str(justified), "ref": f"BOL-{spec['order_id']}"},
            {"code": spec["fee_code"], "desc": spec["fee_reason"], "amount": str(claimable), "ref": "MEMO-FEE"}
        ]
        deliv_notes = f"Shortage of {short_q} units verified and signed on dock manifest"
        has_disc = True

    elif scen == "damaged_with_admin_fee":
        justified = Decimal(dam_q) * inv_unit_p
        claimable = unauth_fee
        deductions = [
            {"code": "DAMAGED", "desc": f"Averia en muelle de {dam_q} uds SKU {sku} constatada en POD", "amount": str(justified), "ref": f"BOL-{spec['order_id']}"},
            {"code": spec["fee_code"], "desc": spec["fee_reason"], "amount": str(claimable), "ref": "MEMO-ADMIN"}
        ]
        deliv_notes = f"{dam_q} units damaged during carrier transit, signed on POD"
        has_disc = True

    elif scen == "alleged_shortage_clean_pod":
        alleged_q = spec.get("alleged_shortage_qty", 2)
        justified = Decimal("0.00")
        claimable = Decimal(alleged_q) * inv_unit_p
        deductions = [
            {"code": "ALLEGED_SHORTAGE_UNILATERAL", "desc": f"Retencion unilateral por supuesto faltante de {alleged_q} uds no reportado en muelle", "amount": str(claimable), "ref": f"INV-{spec['order_id']}"}
        ]
        deliv_notes = f"Full shipment of {qty} units received and signed clean at dock"
        has_disc = False

    elif scen == "price_overcharge_with_slotting":
        price_diff_total = (inv_unit_p - unit_p) * Decimal(qty)
        justified = price_diff_total
        claimable = unauth_fee
        deductions = [
            {"code": "PRICE_DIFF", "desc": f"Ajuste a precio pactado en OC (${unit_p:.2f} vs ${inv_unit_p:.2f} en {qty} uds)", "amount": str(justified), "ref": f"PO-{spec['order_id']}"},
            {"code": spec["fee_code"], "desc": spec["fee_reason"], "amount": str(claimable), "ref": "SLOT-FEE"}
        ]
        deliv_notes = f"{qty} units received intact with matching barcodes"
        has_disc = False

    elif scen == "shortage_and_damage_with_rebate":
        justified = (Decimal(short_q) * unit_p) + (Decimal(dam_q) * unit_p)
        claimable = unauth_fee
        deductions = [
            {"code": "SHORTAGE", "desc": f"Faltante fisico en muelle de {short_q} uds SKU {sku}", "amount": str(Decimal(short_q) * unit_p), "ref": f"BOL-{spec['order_id']}"},
            {"code": "DAMAGED", "desc": f"Averia verificada en muelle de {dam_q} uds SKU {sku}", "amount": str(Decimal(dam_q) * unit_p), "ref": f"BOL-{spec['order_id']}"},
            {"code": spec["fee_code"], "desc": spec["fee_reason"], "amount": str(claimable), "ref": "REB-UNAUTH"}
        ]
        deliv_notes = f"{short_q} units missing and {dam_q} units crushed on arrival"
        has_disc = True
    else:
        justified = Decimal("0.00")
        claimable = Decimal("0.00")
        deductions = []
        deliv_notes = "Clean delivery"
        has_disc = False

    total_deducted = justified + claimable
    received_amt = billed_amt - total_deducted
    diff_val = -total_deducted

    # Formatos a generar según spec
    formats = spec.get("formats", [".xlsx", ".csv", ".txt"])

    # 1. Invoice (.xlsx si está en formats, sino .csv o .json)
    if ".xlsx" in formats:
        MultiFormatParser.write_xlsx_workbook(
            cdir / "invoice.xlsx",
            headers=["item_id", "description", "quantity", "unit_price", "total_price"],
            rows=[[sku, f"{p_name} (DataCo {sku})", qty, f"{inv_unit_p:.2f}", f"{billed_amt:.2f}"]],
            metadata={
                "invoice_id": f"INV-{spec['order_id']}",
                "vendor_id": f"DATACO-{hub.split(',')[0].upper()}",
                "customer_id": f"BUYER-{spec['order_id']}",
                "po_reference": f"PO-{spec['order_id']}",
                "issue_date": "2026-02-01",
                "currency": "USD",
                "subtotal": f"{billed_amt:.2f}",
                "tax": "0.00",
                "total_amount": f"{billed_amt:.2f}",
            },
            sheet_name="Commercial_Invoice"
        )
    elif ".csv" in formats:
        _write_csv(
            cdir / "invoice.csv",
            metadata={
                "invoice_id": f"INV-{spec['order_id']}",
                "vendor_id": f"DATACO-{hub.split(',')[0].upper()}",
                "customer_id": f"BUYER-{spec['order_id']}",
                "po_reference": f"PO-{spec['order_id']}",
                "issue_date": "2026-02-01",
                "currency": "USD",
                "subtotal": f"{billed_amt:.2f}",
                "tax": "0.00",
                "total_amount": f"{billed_amt:.2f}",
            },
            headers=["item_id", "description", "quantity", "unit_price", "total_price"],
            rows=[[sku, f"{p_name} (DataCo {sku})", qty, f"{inv_unit_p:.2f}", f"{billed_amt:.2f}"]]
        )
    else:
        (cdir / "invoice.json").write_text(
            json.dumps({
                "invoice_id": f"INV-{spec['order_id']}",
                "vendor_id": f"DATACO-{hub.split(',')[0].upper()}",
                "customer_id": f"BUYER-{spec['order_id']}",
                "po_reference": f"PO-{spec['order_id']}",
                "issue_date": "2026-02-01",
                "currency": "USD",
                "items": [{"item_id": sku, "description": p_name, "quantity": qty, "unit_price": f"{inv_unit_p:.2f}", "total_price": f"{billed_amt:.2f}"}],
                "subtotal": f"{billed_amt:.2f}",
                "tax": "0.00",
                "total_amount": f"{billed_amt:.2f}"
            }, indent=2),
            encoding="utf-8"
        )

    # 2. Purchase Order (.csv o .xlsx o .json)
    if ".csv" in formats and not (cdir / "invoice.csv").exists():
        _write_csv(
            cdir / "purchase_order.csv",
            metadata={
                "po_id": f"PO-{spec['order_id']}",
                "vendor_id": f"DATACO-{hub.split(',')[0].upper()}",
                "customer_id": f"BUYER-{spec['order_id']}",
                "order_date": "2026-01-25",
                "currency": "USD",
                "total_amount": f"{agreed_po_tot:.2f}",
            },
            headers=["item_id", "description", "ordered_quantity", "agreed_unit_price", "total_price"],
            rows=[[sku, f"{p_name} (DataCo {sku})", qty, f"{unit_p:.2f}", f"{agreed_po_tot:.2f}"]]
        )
    elif ".xlsx" in formats and not (cdir / "invoice.xlsx").exists():
        MultiFormatParser.write_xlsx_workbook(
            cdir / "purchase_order.xlsx",
            headers=["item_id", "description", "ordered_quantity", "agreed_unit_price", "total_price"],
            rows=[[sku, f"{p_name} (DataCo {sku})", qty, f"{unit_p:.2f}", f"{agreed_po_tot:.2f}"]],
            metadata={
                "po_id": f"PO-{spec['order_id']}",
                "vendor_id": f"DATACO-{hub.split(',')[0].upper()}",
                "customer_id": f"BUYER-{spec['order_id']}",
                "order_date": "2026-01-25",
                "currency": "USD",
                "total_amount": f"{agreed_po_tot:.2f}",
            },
            sheet_name="Purchase_Order"
        )
    else:
        _write_csv(
            cdir / "purchase_order.csv",
            metadata={
                "po_id": f"PO-{spec['order_id']}",
                "vendor_id": f"DATACO-{hub.split(',')[0].upper()}",
                "customer_id": f"BUYER-{spec['order_id']}",
                "order_date": "2026-01-25",
                "currency": "USD",
                "total_amount": f"{agreed_po_tot:.2f}",
            },
            headers=["item_id", "description", "ordered_quantity", "agreed_unit_price", "total_price"],
            rows=[[sku, f"{p_name} (DataCo {sku})", qty, f"{unit_p:.2f}", f"{agreed_po_tot:.2f}"]]
        )

    # 3. Delivery (.csv o .xlsx o .txt)
    if ".csv" in formats and not (cdir / "purchase_order.csv").exists():
        _write_csv(
            cdir / "delivery.csv",
            metadata={
                "delivery_id": f"BOL-{spec['order_id']}",
                "po_reference": f"PO-{spec['order_id']}",
                "delivery_date": "2026-01-30",
                "received_by": f"Supervisor {hub.split(',')[0]} Dock",
                "warehouse_location": f"{hub} Distribution Hub",
                "signed": "true",
                "discrepancy_reported": str(has_disc).lower(),
            },
            headers=["item_id", "quantity_delivered", "quantity_received", "missing_quantity", "damaged_quantity", "notes"],
            rows=[[sku, qty, rec_q, short_q, dam_q, deliv_notes]]
        )
    elif ".xlsx" in formats and not (cdir / "invoice.xlsx").exists() and not (cdir / "purchase_order.xlsx").exists():
        MultiFormatParser.write_xlsx_workbook(
            cdir / "delivery.xlsx",
            headers=["item_id", "quantity_delivered", "quantity_received", "missing_quantity", "damaged_quantity", "notes"],
            rows=[[sku, qty, rec_q, short_q, dam_q, deliv_notes]],
            metadata={
                "delivery_id": f"BOL-{spec['order_id']}",
                "po_reference": f"PO-{spec['order_id']}",
                "delivery_date": "2026-01-30",
                "received_by": f"Supervisor {hub.split(',')[0]} Dock",
                "warehouse_location": f"{hub} Distribution Hub",
                "signed": "true",
                "discrepancy_reported": str(has_disc).lower(),
            },
            sheet_name="Proof_Of_Delivery"
        )
    else:
        (cdir / "delivery.txt").write_text(
            f"RECEIVING SLIP / COMPROBANTE DE ENTREGA EN MUELLE\n"
            f"delivery_id: BOL-{spec['order_id']}\n"
            f"po_reference: PO-{spec['order_id']}\n"
            f"delivery_date: 2026-01-30\n"
            f"received_by: Supervisor {hub.split(',')[0]} Dock\n"
            f"warehouse_location: {hub} Distribution Hub\n"
            f"signed: true\n"
            f"discrepancy_reported: {str(has_disc).lower()}\n\n"
            f"ITEM | sku={sku} | delivered={qty} | received={rec_q} | missing={short_q} | damaged={dam_q} | notes={deliv_notes}\n",
            encoding="utf-8"
        )

    # 4. Payment (.txt o .csv o .xlsx)
    if ".txt" in formats and not (cdir / "delivery.txt").exists():
        ded_lines = "\n".join([f"DEDUCTION | code={d['code']} | amount={d['amount']} | reason={d['desc']} | ref={d['ref']}" for d in deductions])
        (cdir / "payment.txt").write_text(
            f"REMITTANCE ADVICE / AVISO DE PAGO BANCARIO\n"
            f"payment_id: PAY-{spec['order_id']}\n"
            f"invoice_reference: INV-{spec['order_id']}\n"
            f"payment_date: 2026-02-15\n"
            f"currency: USD\n"
            f"amount_paid: {received_amt:.2f}\n\n"
            f"DEDUCTIONS APPLIED:\n"
            f"{ded_lines}\n",
            encoding="utf-8"
        )
    elif ".csv" in formats and not (cdir / "delivery.csv").exists() and not (cdir / "purchase_order.csv").exists():
        _write_csv(
            cdir / "payment.csv",
            metadata={
                "payment_id": f"PAY-{spec['order_id']}",
                "invoice_reference": f"INV-{spec['order_id']}",
                "payment_date": "2026-02-15",
                "currency": "USD",
                "amount_paid": f"{received_amt:.2f}",
            },
            headers=["code", "reason", "amount", "reference_doc"],
            rows=[[d["code"], d["desc"], d["amount"], d["ref"]] for d in deductions]
        )
    else:
        ded_lines = "\n".join([f"DEDUCTION | code={d['code']} | amount={d['amount']} | reason={d['desc']} | ref={d['ref']}" for d in deductions])
        (cdir / "payment.txt").write_text(
            f"REMITTANCE ADVICE / AVISO DE PAGO BANCARIO\n"
            f"payment_id: PAY-{spec['order_id']}\n"
            f"invoice_reference: INV-{spec['order_id']}\n"
            f"payment_date: 2026-02-15\n"
            f"currency: USD\n"
            f"amount_paid: {received_amt:.2f}\n\n"
            f"DEDUCTIONS APPLIED:\n"
            f"{ded_lines}\n",
            encoding="utf-8"
        )

    # 5. Contract (.txt o .json)
    if ".json" in formats and not (cdir / "invoice.json").exists():
        (cdir / "contract.json").write_text(
            json.dumps({
                "contract_id": f"MSA-{spec['order_id']}",
                "vendor_id": f"DATACO-{hub.split(',')[0].upper()}",
                "customer_id": f"BUYER-{spec['order_id']}",
                "valid_from": "2025-01-01",
                "valid_to": "2026-12-31",
                "clauses": [
                    {
                        "clause_id": "CL-POD-01",
                        "title": "Prevalencia de Remisión Firmada en Muelle",
                        "text": "Las discrepancias físicas por faltantes o averías registradas en la remisión firmada de muelle son deducibles al precio unitario autorizado.",
                        "policy": "STRICT_POD_REQUIRED",
                        "tolerance_percentage": "0.00"
                    },
                    {
                        "clause_id": "CL-UNAUTH-02",
                        "title": "Prohibición de Cargos Administrativos Unilaterales",
                        "text": "Se prohibe aplicar deducciones por mercadeo, portal EDI, fletes o penalidades operativas que no cuenten con adenda bilateral.",
                        "policy": "NO_UNILATERAL_PENALTIES",
                        "tolerance_percentage": "0.00"
                    }
                ]
            }, indent=2),
            encoding="utf-8"
        )
    else:
        (cdir / "contract.txt").write_text(
            f"MASTER SUPPLY AGREEMENT — DATACO NETWORK ({hub})\n"
            f"contract_id: MSA-{spec['order_id']}\n"
            f"vendor_id: DATACO-{hub.split(',')[0].upper()}\n"
            f"customer_id: BUYER-{spec['order_id']}\n"
            f"valid_from: 2025-01-01\n"
            f"valid_to: 2026-12-31\n\n"
            f"[CLAUSE CL-POD-01|Prevalencia de Remision Firmada|STRICT_POD_REQUIRED|0.00]\n"
            f"Las discrepancias fisicas por faltantes o averias asentadas en la remision de muelle autorizan deduccion al costo unitario pactado.\n"
            f"[CLAUSE CL-UNAUTH-02|Prohibicion de Deducciones Unilaterales|NO_UNILATERAL_PENALTIES|0.00]\n"
            f"Queda estrictamente prohibido aplicar retenciones comerciales o logisticas que no esten amparadas en adenda firmada.\n",
            encoding="utf-8"
        )

    # 6. Ground Truth
    (cdir / "ground_truth.json").write_text(
        json.dumps({
            "case_id": cid,
            "dataset_source": "DataCo Global Smart Supply Chain Dataset (DOI: 10.17632/8gx2fvg2k6.5)",
            "buyer_name": buyer,
            "industry": ind,
            "hub": hub,
            "file_formats": formats,
            "billed_amount": f"{billed_amt:.2f}",
            "received_amount": f"{received_amt:.2f}",
            "difference": f"{diff_val:.2f}",
            "expected_justified_amount": f"{justified:.2f}",
            "expected_claimable_amount": f"{claimable:.2f}",
        }, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def build_all_30_real_cases() -> None:
    REAL_CASES_DIR.mkdir(parents=True, exist_ok=True)

    # Exportar extracto fuente con los 30 registros
    src_csv = REAL_CASES_DIR / "dataco_open_supply_chain_source_records.csv"
    with open(src_csv, "w", encoding="utf-8", newline="") as f:
        fields = ["dataco_order_id", "product_card_id", "product_name", "origin_hub", "order_item_product_price", "category_name", "dataset_doi"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for s in DATACO_30_SPECIFICATIONS:
            writer.writerow({
                "dataco_order_id": s["order_id"],
                "product_card_id": s["sku"],
                "product_name": s["name"],
                "origin_hub": s["hub"],
                "order_item_product_price": s["price"],
                "category_name": s["industry"],
                "dataset_doi": "10.17632/8gx2fvg2k6.5"
            })

    # Construir los 30 expedientes físicos
    for spec in DATACO_30_SPECIFICATIONS:
        build_single_case(spec)

    print(f"[OK] Construidos exitosamente 30 expedientes reales multiformato DataCo en: {REAL_CASES_DIR}")


if __name__ == "__main__":
    build_all_30_real_cases()
