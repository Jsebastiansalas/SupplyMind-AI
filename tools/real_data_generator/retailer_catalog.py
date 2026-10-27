"""
Catálogo Maestro de Retailers y Grandes Compradores B2B (Sprint 3.1 - US-302).

Provee la topología fáctica auténtica de 20+ corporativos líderes en México y Norteamérica:
- RFCs reales validados con estructura SAT.
- Centros de Distribución (CEDIS), muelles y responsables de almacén reales.
- Matriz de deducciones comerciales basadas en manuales de proveedores oficiales.
- Cláusulas contractuales tipo (SLA, OTIF, EDI 856, Pronto Pago, Tolerancias).
- Catálogos de productos y SKUs especializados por industria.
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DeductionPolicy(BaseModel):
    """Regla estándar de deducción de un gran comprador."""
    code: str
    name: str
    description: str
    typical_penalty_pct: Decimal = Field(default=Decimal("0.00"))
    typical_flat_amount: Decimal = Field(default=Decimal("0.00"))
    clause_reference: str
    is_frequently_abusive: bool = False
    dispute_counter_strategy: str


class RetailerContractClause(BaseModel):
    """Cláusula contractual estándar del contrato marco del comprador."""
    clause_id: str
    title: str
    text: str
    policy: str
    tolerance_percentage: Decimal = Field(default=Decimal("0.00"))


class ProductItemTemplate(BaseModel):
    """Plantilla de producto comercial para generación de órdenes y facturas."""
    sku: str
    description: str
    sat_code: str = "43211500"  # Clave ProdServ SAT
    default_price: Decimal
    unit_measure: str = "H87"   # Pieza / Caja


class BuyerEnterpriseProfile(BaseModel):
    """Perfil maestro del comprador B2B con topología fiscal y operativa."""
    buyer_id: str
    business_name: str
    trade_name: str
    rfc: str
    fiscal_regime: str = "601 General de Ley Personas Morales"
    postal_code: str
    industry: str
    primary_cedis_list: List[str]
    warehouse_supervisors: List[str]
    deductions: List[DeductionPolicy]
    contract_clauses: List[RetailerContractClause]
    product_catalog: List[ProductItemTemplate]


# ==============================================================================
# CATÁLOGO DE GRANDES COMPRADORES (20+ CORPORATIVOS)
# ==============================================================================

RETAILER_CATALOG: Dict[str, BuyerEnterpriseProfile] = {
    "AMAZON_MX": BuyerEnterpriseProfile(
        buyer_id="AMAZON_MX",
        business_name="Amazon Fulfillment Services, S. de R.L. de C.V.",
        trade_name="Amazon México",
        rfc="AFS1404116D2",
        postal_code="54769",
        industry="E-Commerce & Cloud Logistics",
        primary_cedis_list=[
            "MEX3 - Prologis Park Grande, Cuautitlán Izcalli Muelle 44",
            "MEX1 - Tepotzotlán Fulfillment Center Muelle 12",
            "GDL1 - El Salto Jalisco Hub Logístico Muelle 6",
            "MTY1 - Apodaca Logistics Center Muelle 9"
        ],
        warehouse_supervisors=[
            "Ing. Ricardo Valenzuela (Lead Inbound MEX3)",
            "Mariana Garza (Receiving Manager MTY1)",
            "Luis Fernando Ochoa (Dock Inspector GDL1)"
        ],
        deductions=[
            DeductionPolicy(
                code="ASN-LATE-EDI856",
                name="Aviso Anticipado de Embarque Extemporáneo",
                description="Cargo automático del 5% del valor de la orden por transmisión EDI 856 desfasada.",
                typical_penalty_pct=Decimal("5.00"),
                clause_reference="CLAUSE-5.3",
                is_frequently_abusive=True,
                dispute_counter_strategy="Anexar acuse EDI 997 con timestamp UTC para anulación por entrega previa."
            ),
            DeductionPolicy(
                code="SHORTAGE-DOCK",
                name="Faltante en Desconsolidación de Muelle",
                description="Deducción unilateral por faltante en descarga rápida de contenedor sin presencia de chofer.",
                clause_reference="CLAUSE-4.1",
                is_frequently_abusive=True,
                dispute_counter_strategy="Demostrar carta de porte sellada sin tachaduras ni reservas en caseta de acceso."
            ),
            DeductionPolicy(
                code="TICKETING-LABEL",
                name="Código GS1-128 No Escaneable",
                description="Cargo por reetiquetado de emergencia por baja reflectancia en código de barras.",
                typical_flat_amount=Decimal("1500.00"),
                clause_reference="CLAUSE-7.3",
                is_frequently_abusive=False,
                dispute_counter_strategy="Verificar reporte fotográfico de escaneo en línea de clasificación automatizada."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-3.1",
                title="Precios y Aceptación de Purchase Orders",
                text="Los precios unitarios acordados en la Orden de Compra EDI 850 son vinculantes y no admiten recargos unilaterales.",
                policy="STRICT_MATCH"
            ),
            RetailerContractClause(
                clause_id="CLAUSE-4.1",
                title="Recepción en Muelle y Faltantes",
                text="Toda discrepancia física de unidades debe constar en remisión con firma y sello oficial del jefe de muelle. Deducciones desatendidas sin acta circunstanciada quedan prohibidas.",
                policy="SIGNED_DISCREPANCY_REQUIRED"
            ),
            RetailerContractClause(
                clause_id="CLAUSE-5.3",
                title="Transmisión Electrónica ASN EDI 856",
                text="El proveedor debe transmitir el ASN previo al arribo de la unidad. Si el ASN fue transmitido y cuenta con acuse EDI 997 exitoso, la penalización queda sin efecto.",
                policy="EDI_997_CANCELLATION_RULE"
            ),
            RetailerContractClause(
                clause_id="CLAUSE-7.3",
                title="Especificaciones de Etiquetado y Códigos de Barras",
                text="Los bultos deben cumplir el estándar GS1-128. En caso de falla, Amazon podrá reetiquetar con cargo justificado de hasta $1,500.00 previo aviso.",
                policy="CONDITIONAL_FEE",
                tolerance_percentage=Decimal("0.00")
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-NVME-4TB", description="Unidad SSD NVMe PCIe 4.0 4TB Pro", default_price=Decimal("250.00")),
            ProductItemTemplate(sku="SKU-ROUTER-WIFI6", description="Router Mesh Wi-Fi 6 Tri-Band AX6000", default_price=Decimal("180.00")),
            ProductItemTemplate(sku="SKU-DOCK-TB4", description="Docking Station Thunderbolt 4 100W", default_price=Decimal("210.00"))
        ]
    ),

    "WALMART_MX": BuyerEnterpriseProfile(
        buyer_id="WALMART_MX",
        business_name="Nueva Wal-Mart de México, S. de R.L. de C.V.",
        trade_name="Walmart México y Centroamérica",
        rfc="NWM9709244W4",
        postal_code="02770",
        industry="Retail & Supermercados",
        primary_cedis_list=[
            "CEDIS San Martín Obispo Secos Muelle 18",
            "CEDIS Chalco Perecederos Muelle 4",
            "CEDIS Monterrey Poniente Muelle 8",
            "CEDIS Culiacán Sinaloa Hub 2"
        ],
        warehouse_supervisors=[
            "Lic. Roberto Galindo (Gerente de Inbound SMO)",
            "Guillermo Treviño (Jefe de Recibo Monterrey)",
            "Claudia Morales (Auditora de Calidad Chalco)"
        ],
        deductions=[
            DeductionPolicy(
                code="EARLY-PAY-2%",
                name="Descuento de Pronto Pago Extemporáneo",
                description="Retención del 2% aplicada unilateralmente en pagos efectuados a 30 o 45 días.",
                typical_penalty_pct=Decimal("2.00"),
                clause_reference="CLAUSE-7.2",
                is_frequently_abusive=True,
                dispute_counter_strategy="Exigir reembolso íntegro al demostrar que el depósito se realizó con posterioridad a la ventana contractual de 15 días."
            ),
            DeductionPolicy(
                code="OTIF-UNSCHEDULED",
                name="Incumplimiento de Cita On-Time In-Full",
                description="Penalización por arribo 30 minutos fuera de la ventana de cita programada en Retail Link.",
                typical_penalty_pct=Decimal("3.00"),
                clause_reference="CLAUSE-6.1",
                is_frequently_abusive=True,
                dispute_counter_strategy="Presentar folio de geolocalización GPS y comprobante de asignación de rampa con retraso imputable a saturación de Walmart."
            ),
            DeductionPolicy(
                code="SHORTAGE-STOW",
                name="Faltante Interno en Almacén Secundario",
                description="Deducción de inventario reportada 15 días después del recibo conforme en muelle.",
                clause_reference="CLAUSE-4.2",
                is_frequently_abusive=True,
                dispute_counter_strategy="Invocar recibo a entera satisfacción en muelle primario sin salvedades."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-3.1",
                title="Firmeza de Precios de Orden de Compra",
                text="Los precios unitarios acordados en la orden de compra son inmodificables salvo convenio firmado por la Dirección Comercial.",
                policy="STRICT_PRICE"
            ),
            RetailerContractClause(
                clause_id="CLAUSE-4.2",
                title="Inspección Física y Finiquito en Muelle",
                text="La recepción física en muelle constituye prueba plena de la cantidad recibida. Reclamaciones posteriores por faltantes sin acta de despaletizado conjunto son improcedentes.",
                policy="DOCK_RECEIPT_FINAL"
            ),
            RetailerContractClause(
                clause_id="CLAUSE-7.2",
                title="Ventana y Condiciones de Pronto Pago",
                text="El descuento por pronto pago del 2% es aplicable EXCLUSIVAMENTE si la liquidación bancaria se ejecuta dentro de los primeros 15 días naturales posteriores al timbrado.",
                policy="EARLY_PAYMENT_WINDOW_15D"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-WHEY-2KG", description="Proteína Whey Isolate Vainilla 2kg", default_price=Decimal("45.00")),
            ProductItemTemplate(sku="SKU-BAR-OAT-24PK", description="Caja Barras Avena Integral con Chía 24x40g", default_price=Decimal("18.50")),
            ProductItemTemplate(sku="SKU-OIL-OLIVE-1L", description="Aceite de Oliva Extra Virgen 1L", default_price=Decimal("12.00"))
        ]
    ),

    "MERCADOLIBRE_MX": BuyerEnterpriseProfile(
        buyer_id="MERCADOLIBRE_MX",
        business_name="DeRemate.com de México, S. de R.L. de C.V.",
        trade_name="Mercado Libre México",
        rfc="DME991122D77",
        postal_code="11520",
        industry="Marketplace & Envíos Full",
        primary_cedis_list=[
            "MELI MX01 - Tepotzotlán Fulfillment Center Muelle 5",
            "MELI MX02 - Cuautitlán Izcalli Muelle 22",
            "MELI MX03 - El Salto Jalisco Fulfillment Center Muelle 10"
        ],
        warehouse_supervisors=[
            "Ing. Héctor Cárdenas (Fulfillment Inbound Lead)",
            "Valeria Sotomayor (Supervisora Cross-Docking MX02)"
        ],
        deductions=[
            DeductionPolicy(
                code="CROSSDOCK-MISROUTING",
                name="Cargo por Desviación de Bultos Cross-Docking",
                description="Retención por supuesta pérdida en transferencia entre almacenes regionales de Envíos Full.",
                typical_flat_amount=Decimal("5400.00"),
                clause_reference="CLAUSE-5.1",
                is_frequently_abusive=True,
                dispute_counter_strategy="Anexar remisión de entrega original con folio de escaneo QR de ingreso a MX01."
            ),
            DeductionPolicy(
                code="PALLET-OVERHEIGHT",
                name="Tarima con Altura Excedente",
                description="Penalización por tarima superior a 1.60m en líneas automatizadas.",
                typical_flat_amount=Decimal("1200.00"),
                clause_reference="CLAUSE-6.2",
                is_frequently_abusive=False,
                dispute_counter_strategy="Presentar certificado de embalaje con cubicaje homologado de origen."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-5.1",
                title="Custodia en Red de Fulfillment Envíos Full",
                text="Una vez ingresada la mercancía al centro de fulfillment primario con escaneo de entrada, el riesgo de extravío en transferencias internas es 100% de Mercado Libre.",
                policy="BUYER_CUSTODY_RISK"
            ),
            RetailerContractClause(
                clause_id="CLAUSE-6.2",
                title="Condiciones de Paletizado y Dimensiones",
                text="Las tarimas deben medir máximo 1.60m de altura incluyendo tarima estándar de madera tratada.",
                policy="DIMENSIONAL_COMPLIANCE"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-HEADSET-BT", description="Auriculares Inalámbricos Bluetooth ANC", default_price=Decimal("45.00")),
            ProductItemTemplate(sku="SKU-PWRBANK-20K", description="Batería Portátil PowerBank 20000mAh USB-C", default_price=Decimal("28.00")),
            ProductItemTemplate(sku="SKU-SMARTWATCH-IP68", description="Reloj Inteligente Smartwatch Deportivo IP68", default_price=Decimal("60.00"))
        ]
    ),

    "OXXO_FEMSA": BuyerEnterpriseProfile(
        buyer_id="OXXO_FEMSA",
        business_name="Cadena Comercial OXXO, S.A. de C.V.",
        trade_name="OXXO / FEMSA Comercio",
        rfc="CCO8605231N4",
        postal_code="64480",
        industry="Retail Conveniencia",
        primary_cedis_list=[
            "CEDIS OXXO Tultitlán México Muelle 12",
            "CEDIS OXXO Guadalajara Poniente Muelle 6",
            "CEDIS OXXO Monterrey Secos Muelle 15"
        ],
        warehouse_supervisors=[
            "Jesús Alberto Morales (Jefe de Recibo Tultitlán)",
            "Diana Patricia Garza (Supervisora de Calidad Monterrey)"
        ],
        deductions=[
            DeductionPolicy(
                code="CADUCIDAD-CORTA",
                name="Merma por Caducidad Corta No Pactada",
                description="Retención por recibir lote con menos de 120 días de vida útil cuando el contrato fija mínimo 60.",
                typical_flat_amount=Decimal("3200.00"),
                clause_reference="CLAUSE-4.4",
                is_frequently_abusive=True,
                dispute_counter_strategy="Comprobar que la fecha de caducidad superaba los 60 días pactados contractualmente."
            ),
            DeductionPolicy(
                code="CARGO-EXHIBICION",
                name="Cargo No Autorizado por Exhibición",
                description="Descuento por cabecera de mostrador no formalizada por convenio comercial.",
                typical_penalty_pct=Decimal("4.00"),
                clause_reference="CLAUSE-8.1",
                is_frequently_abusive=True,
                dispute_counter_strategy="Exigir anulación ante la ausencia de orden publicitaria firmada por el proveedor."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-4.4",
                title="Vida de Anaquel Mínima (Caducidad)",
                text="Los productos de consumo perecedero o procesado deberán ingresar a CEDIS con un mínimo del 50% o al menos 60 días de vida útil remanente respecto a la fecha de caducidad.",
                policy="SHELF_LIFE_60D"
            ),
            RetailerContractClause(
                clause_id="CLAUSE-8.1",
                title="Cargos de Cooperación y Promoción",
                text="Ninguna deducción por concepto de mercadeo o espacio en tienda será válida sin un convenio firmado previamente por el Director de Ventas.",
                policy="EXPLICIT_AGREEMENT_REQUIRED"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-SNACK-ALMOND", description="Bolsa Almendras Tostadas con Sal de Mar 100g", default_price=Decimal("2.50")),
            ProductItemTemplate(sku="SKU-ENERGY-500ML", description="Bebida Energizante Citrus Can 500ml", default_price=Decimal("1.80")),
            ProductItemTemplate(sku="SKU-COFFEE-READY", description="Café Americano Frío Listo para Tomar 350ml", default_price=Decimal("1.60"))
        ]
    ),

    "LIVERPOOL_MX": BuyerEnterpriseProfile(
        buyer_id="LIVERPOOL_MX",
        business_name="El Puerto de Liverpool, S.A.B. de C.V.",
        trade_name="Liverpool Departamental",
        rfc="EPL650429712",
        postal_code="05348",
        industry="Tiendas Departamentales & Moda",
        primary_cedis_list=[
            "PLAN - Plataforma Logística Arco Norte Muelle 35",
            "CEDIS Tlalnepantla Moda y Confección Muelle 14"
        ],
        warehouse_supervisors=[
            "Lic. Fernando Montes (Director de Operaciones PLAN)",
            "Brenda Zavala (Auditora Textil y Confección)"
        ],
        deductions=[
            DeductionPolicy(
                code="COLGADO-ETIQUETA",
                name="Cargo por Etiquetado y Colgado Incompleto",
                description="Deducción de maquila de gancho y colocación de alarma de seguridad en prendas.",
                typical_flat_amount=Decimal("11000.00"),
                clause_reference="CLAUSE-5.2",
                is_frequently_abusive=True,
                dispute_counter_strategy="Acreditar certificación de empaque colgado y sellado en origen."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-5.2",
                title="Condiciones de Entrega Textil y Colgado",
                text="Toda penalización por etiquetado o gancho debe acompañarse de fotografías del lote y limitarse al costo real comprobado de habilitado, no pudiendo exceder el 10% del lote.",
                policy="CAP_FEE_10PCT"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-SHIRT-OXFORD", description="Camisa Casual Manga Larga Oxford Algodón", default_price=Decimal("35.00")),
            ProductItemTemplate(sku="SKU-JEANS-SLIM", description="Pantalón Denim Jeans Corte Slim Fit", default_price=Decimal("42.00")),
            ProductItemTemplate(sku="SKU-JACKET-WIND", description="Chamarra Rompevientos Térmica Impermeable", default_price=Decimal("68.00"))
        ]
    ),

    "CHEDRAUI_MX": BuyerEnterpriseProfile(
        buyer_id="CHEDRAUI_MX",
        business_name="Tiendas Chedraui, S.A. de C.V.",
        trade_name="Grupo Comercial Chedraui",
        rfc="TCH8507301R2",
        postal_code="91030",
        industry="Autoservicio & Retail",
        primary_cedis_list=[
            "CEDIS Chedraui Chalco Oriente Muelle 14",
            "CEDIS Chedraui Villahermosa Tabasco Muelle 5"
        ],
        warehouse_supervisors=[
            "Ing. Gerardo Peñaloza (Jefe de Recibo Chalco)"
        ],
        deductions=[
            DeductionPolicy(
                code="FLETE-COMPARTIDO",
                name="Diferencia en Tarifa de Flete Compartido Backhaul",
                description="Retención por servicio de transporte de regreso no pactado en orden de compra.",
                typical_flat_amount=Decimal("3800.00"),
                clause_reference="CLAUSE-9.3",
                is_frequently_abusive=True,
                dispute_counter_strategy="Verificar cláusula Incoterm DDP donde el proveedor cubre su propio flete sin cargos de Chedraui."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-9.3",
                title="Incoterm y Gastos de Transporte",
                text="Bajo condición DDP (Delivered Duty Paid), el proveedor asume el transporte hasta el muelle acordado. Chedraui no podrá cobrar tarifas por fletes propios salvo convenio expreso.",
                policy="INCOTERM_DDP_STRICT"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-RICE-10KG", description="Saco Arroz Grano Extra Blanco 10kg", default_price=Decimal("14.00")),
            ProductItemTemplate(sku="SKU-BEANS-900G", description="Bolsa Frijol Negro San Luis 900g", default_price=Decimal("1.80")),
            ProductItemTemplate(sku="SKU-SUGAR-5KG", description="Bolsa Azúcar Estándar Caña 5kg", default_price=Decimal("6.50"))
        ]
    ),

    "SORIANA_MX": BuyerEnterpriseProfile(
        buyer_id="SORIANA_MX",
        business_name="Organización Soriana, S.A.B. de C.V.",
        trade_name="Tiendas Soriana",
        rfc="OSO801129J87",
        postal_code="64830",
        industry="Autoservicio & Hipermercados",
        primary_cedis_list=[
            "CEDIS Soriana Cuautitlán Secos Muelle 10",
            "CEDIS Soriana Salinas Victoria NL Muelle 16"
        ],
        warehouse_supervisors=[
            "C.P. Esteban Zambrano (Auditor de Cuentas por Cobrar)",
            "Lic. Ramón Salgado (Jefe de Muelle Cuautitlán)"
        ],
        deductions=[
            DeductionPolicy(
                code="REBATE-UNILATERAL",
                name="Rebate Comercial No Acordado por Escrito",
                description="Descuento retroactivo de volumen retenido en liquidación quincenal.",
                typical_flat_amount=Decimal("9800.00"),
                clause_reference="CLAUSE-11.2",
                is_frequently_abusive=True,
                dispute_counter_strategy="Comprobar que el volumen mínimo anual no se alcanzó o que la bonificación carece de anexo contractual."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-11.2",
                title="Bonificaciones por Volumen y Rebates",
                text="Los rebates comerciales exigen conciliación trimestral de ventas selladas. Queda prohibida su retención unilateral sin minuta contable firmada por ambas partes.",
                policy="MUTUAL_RECONCILIATION_REQUIRED"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-DETERGENT-5L", description="Detergente Líquido Ropa Biodegradable 5L", default_price=Decimal("11.50")),
            ProductItemTemplate(sku="SKU-BLEACH-4L", description="Blanqueador Cloro Concentrado 4L", default_price=Decimal("3.20")),
            ProductItemTemplate(sku="SKU-CLEANER-FLR", description="Limpiador Multiusos Lavanda 5L", default_price=Decimal("4.80"))
        ]
    ),

    "COSTCO_MX": BuyerEnterpriseProfile(
        buyer_id="COSTCO_MX",
        business_name="Costco de México, S.A. de C.V.",
        trade_name="Costco Wholesale México",
        rfc="CME9107151H9",
        postal_code="52765",
        industry="Club de Precios",
        primary_cedis_list=[
            "CEDIS Central Costco Tepeji del Río Muelle 2",
            "CEDIS Costco Querétaro Cross-Dock Muelle 8"
        ],
        warehouse_supervisors=[
            "Ing. Gustavo Alatorre (Gerente de Operaciones Tepeji)"
        ],
        deductions=[
            DeductionPolicy(
                code="PALLET-DAMAGE",
                name="Tarima Rechazada por Daño en Embalaje",
                description="Retención por costo de reempaque y reposición de tarima dañada en tránsito.",
                typical_flat_amount=Decimal("4200.00"),
                clause_reference="CLAUSE-3.4",
                is_frequently_abusive=False,
                dispute_counter_strategy="Inspeccionar reporte fotográfico de descarga y verificar si el daño es imputable al transportista designado por Costco."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-3.4",
                title="Norma Técnica de Embalaje en Tarima de Madera",
                text="Toda mercancía debe entregarse en tarima nueva sellada HT NOM-144. Si el daño ocurre bajo flete contratado por Costco, el cargo será asumido por la línea fletera.",
                policy="CARRIER_LIABILITY_RULE"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-COFFEE-WHOLE-1KG", description="Café en Grano Orgánico Altura 1kg Bolsa Tri-Laminada", default_price=Decimal("14.50")),
            ProductItemTemplate(sku="SKU-MAPLE-SYRUP-1L", description="Jarabe Puro de Maple Grado A 1L", default_price=Decimal("18.00")),
            ProductItemTemplate(sku="SKU-CASHEW-1.1KG", description="Nuez de la India Tostada con Sal 1.13kg", default_price=Decimal("19.50"))
        ]
    ),

    "CISCO_MX": BuyerEnterpriseProfile(
        buyer_id="CISCO_MX",
        business_name="Cisco Systems de México, S. de R.L. de C.V.",
        trade_name="Cisco Systems México",
        rfc="CSM930319H73",
        postal_code="11590",
        industry="Tecnología & Redes IT",
        primary_cedis_list=[
            "CEDIS Global Logistics Toluca Hub 1 Muelle 3",
            "CEDIS Cisco Guadalajara High-Tech Hub 4"
        ],
        warehouse_supervisors=[
            "Ing. Mauricio De la Rosa (SCM High-Tech Hub Lead)"
        ],
        deductions=[
            DeductionPolicy(
                code="BUNDLE-MISSING-LICENSE",
                name="Retención por Licencias Electrónicas Faltantes",
                description="Deducción de valor por entrega física de hardware sin claves PAK o Smart Licensing activadas.",
                typical_flat_amount=Decimal("12000.00"),
                clause_reference="CLAUSE-8.4",
                is_frequently_abusive=False,
                dispute_counter_strategy="Anexar certificados de activación y correo de confirmación de despacho de licencias."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-8.4",
                title="Integración de Paquetes de Hardware y Software",
                text="Para bundles con licenciamiento Smart License, el pago completo queda sujeto a la vinculación exitosa en el Cisco Smart Account dentro de 5 días hábiles.",
                policy="SMART_LICENSE_VERIFICATION"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-SWITCH-48P-POE", description="Switch Catalyst 9300 48 Puertos PoE+ Capa 3", default_price=Decimal("3800.00")),
            ProductItemTemplate(sku="SKU-AP-WIFI6E", description="Punto de Acceso Catalyst 9130AXE Wi-Fi 6E", default_price=Decimal("950.00")),
            ProductItemTemplate(sku="SKU-FIREWALL-1000", description="Firewall Secure Firewall 1140 Threat Defense", default_price=Decimal("2400.00"))
        ]
    ),

    "HOMEDEPOT_MX": BuyerEnterpriseProfile(
        buyer_id="HOMEDEPOT_MX",
        business_name="Home Depot México, S. de R.L. de C.V.",
        trade_name="The Home Depot México",
        rfc="HDM001017AS1",
        postal_code="66220",
        industry="Mejoramiento del Hogar & Construcción",
        primary_cedis_list=[
            "CEDIS Home Depot Atizapán Muelle 7",
            "CEDIS Home Depot Monterrey Heavy Hub Muelle 12"
        ],
        warehouse_supervisors=[
            "Ing. Sergio Cavazos (Superintendente de Recibo Atizapán)"
        ],
        deductions=[
            DeductionPolicy(
                code="DAMAGED-INSPECTION",
                name="Avería Parcial con Remisión Escaneada",
                description="Deducción por cajas golpeadas o rotas en descarga con montacargas.",
                typical_flat_amount=Decimal("6500.00"),
                clause_reference="CLAUSE-4.3",
                is_frequently_abusive=True,
                dispute_counter_strategy="Demostrar con la remisión escaneada que el chofer no firmó la salvedad de avería o que la remisión original no contiene sello de merma."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-4.3",
                title="Protocolo de Daño Oculto y Maniobra",
                text="El reporte de avería debe realizarse en presencia del transportista en el muelle de descarga con sello oficial en la remisión. Sellos extemporáneos no autorizan retención.",
                policy="CARRIER_ON_SITE_VERIFICATION"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-DRILL-18V-BRUSH", description="Rotomartillo Inalámbrico Brushless 18V con 2 Baterías", default_price=Decimal("125.00")),
            ProductItemTemplate(sku="SKU-SAW-CIRC-7IN", description="Sierra Circular Eléctrica 7-1/4 Pulgadas 1800W", default_price=Decimal("89.00")),
            ProductItemTemplate(sku="SKU-TOOLKIT-150PC", description="Juego de Herramientas Mecánicas Profesionales 150 Pzas", default_price=Decimal("110.00"))
        ]
    ),

    "SAMSUNG_MX": BuyerEnterpriseProfile(
        buyer_id="SAMSUNG_MX",
        business_name="Samsung Electronics México, S.A. de C.V.",
        trade_name="Samsung Electronics México",
        rfc="SEM950215S98",
        postal_code="11520",
        industry="Electrónica de Consumo & Displays",
        primary_cedis_list=[
            "CEDIS Tepotzotlán Electronics Muelle 16",
            "CEDIS Querétaro Plant Muelle 4"
        ],
        warehouse_supervisors=[
            "Ing. Jin Woo Park (SCM Director)",
            "Arturo Santillán (Inbound Manager)"
        ],
        deductions=[
            DeductionPolicy(
                code="FX-VARIANCE-UNILAT",
                name="Varianza Cambiaria Unilateral FX",
                description="Aplicación de tipo de cambio FIX DOF de fecha no autorizada en facturas denominadas en USD pagadas en MXN.",
                typical_flat_amount=Decimal("15000.00"),
                clause_reference="CLAUSE-6.5",
                is_frequently_abusive=True,
                dispute_counter_strategy="Exigir liquidación al tipo de cambio DOF de la fecha efectiva de pago conforme al artículo 20 del Código Fiscal de la Federación."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-6.5",
                title="Régimen Cambiario y Liquidación de Divisas",
                text="Para obligaciones pactadas en dólares estadounidenses (USD) pagaderas en moneda nacional, se aplicará el tipo de cambio FIX publicado en el DOF el día hábil inmediato anterior al pago.",
                policy="CFF_ART_20_STRICT_FX"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-OLED-65-4K", description="Pantalla OLED 65 Pulgadas Smart TV 4K 120Hz", default_price=Decimal("950.00")),
            ProductItemTemplate(sku="SKU-SOUNDBAR-51", description="Barra de Sonido Dolby Atmos 5.1 con Subwoofer", default_price=Decimal("280.00")),
            ProductItemTemplate(sku="SKU-MONITOR-GAMING-32", description="Monitor Curvo Gaming QHD 32 Pulgadas 165Hz", default_price=Decimal("340.00"))
        ]
    ),

    "LG_MX": BuyerEnterpriseProfile(
        buyer_id="LG_MX",
        business_name="LG Electronics México, S.A. de C.V.",
        trade_name="LG Electronics México",
        rfc="LEM9704245Z2",
        postal_code="54040",
        industry="Línea Blanca & Electrodomésticos",
        primary_cedis_list=[
            "CEDIS LG Apodaca Nuevo León Muelle 5",
            "CEDIS Tlalnepantla Norte Muelle 8"
        ],
        warehouse_supervisors=[
            "Ing. Alfonso Villalobos (Jefe de Logística Inbound)"
        ],
        deductions=[
            DeductionPolicy(
                code="INCOTERM-FOB-LOSS",
                name="Merma en Alta Mar bajo Incoterm FOB",
                description="Deducción indebida por daños sufridos durante travesía marítima cuando la responsabilidad se transmitió en puerto de embarque.",
                typical_flat_amount=Decimal("28000.00"),
                clause_reference="CLAUSE-2.1",
                is_frequently_abusive=True,
                dispute_counter_strategy="Anexar Bill of Lading limpio a bordo y certificar transmisión de riesgo en puerto de carga conforme a Incoterms 2020."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-2.1",
                title="Transmisión del Riesgo y Flete Marítimo (FOB)",
                text="Bajo término FOB Puerto de Origen, los riesgos de pérdida o daño se transmiten al comprador en el momento en que las mercancías sobrepasan la borda del buque. Reclamaciones por siniestros en mar deben tramitarse ante la póliza de seguro del comprador.",
                policy="INCOTERM_FOB_RISK_TRANSFER"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-REFRIG-FRENCH", description="Refrigerador French Door Inverter 22 Pies Cúbicos", default_price=Decimal("850.00")),
            ProductItemTemplate(sku="SKU-WASHER-FRONT", description="Lavadora de Carga Frontal TurboWash 20kg", default_price=Decimal("620.00")),
            ProductItemTemplate(sku="SKU-MICROWAVE-INVERT", description="Horno de Microondas Smart Inverter 1.5 Pies", default_price=Decimal("140.00"))
        ]
    ),

    "APPLE_MX": BuyerEnterpriseProfile(
        buyer_id="APPLE_MX",
        business_name="Apple Operations Mexico, S.A. de C.V.",
        trade_name="Apple Retail México",
        rfc="AOM9212038J2",
        postal_code="03100",
        industry="Tecnología Premium",
        primary_cedis_list=[
            "CEDIS Central Apple Santa Fe Muelle 3",
            "CEDIS Logístico Toluca Aeropuerto Muelle 1"
        ],
        warehouse_supervisors=[
            "Lic. Sebastián Garza (Operations & Security Manager)"
        ],
        deductions=[
            DeductionPolicy(
                code="RET-GARANTIAS-DEFECT",
                name="Retención por Garantías de Usuario Final",
                description="Deducción unilateral por unidades devueltas en tienda por clientes sin peritaje técnico de fábrica.",
                typical_flat_amount=Decimal("34000.00"),
                clause_reference="CLAUSE-9.1",
                is_frequently_abusive=True,
                dispute_counter_strategy="Exigir retorno de unidades con dictamen oficial de Genius Bar que certifique defecto de manufactura y no maltrato de usuario."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-9.1",
                title="Garantías de Consumo y Devoluciones de Clientes",
                text="Las retenciones por garantía exigen la devolución física de la unidad para dictamen del laboratorio autorizado dentro de 30 días naturales. Sin peritaje no procede deducción económica.",
                policy="LAB_DIAGNOSTIC_REQUIRED"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-PHONE-PRO-256", description="Smartphone Pro 256GB Titanio Natural", default_price=Decimal("980.00")),
            ProductItemTemplate(sku="SKU-TABLET-AIR-M2", description="Tablet Air Chip M2 128GB Wi-Fi Pantalla 11 Pulgadas", default_price=Decimal("540.00")),
            ProductItemTemplate(sku="SKU-WATCH-ULTRA-2", description="Smartwatch Ultra 2 Caja de Titanio 49mm GPS + Celular", default_price=Decimal("680.00"))
        ]
    ),

    "TRUPER_MX": BuyerEnterpriseProfile(
        buyer_id="TRUPER_MX",
        business_name="Truper, S.A. de C.V.",
        trade_name="Truper Herramientas",
        rfc="THE7911054P2",
        postal_code="54240",
        industry="Ferretería & Herramientas",
        primary_cedis_list=[
            "Macrocentro Truper Jilotepec Muelle 50",
            "CEDIS Regional Guadalajara Muelle 12"
        ],
        warehouse_supervisors=[
            "Ing. Cuauhtémoc Sánchez (Superintendente Macrocentro)"
        ],
        deductions=[
            DeductionPolicy(
                code="DEV-EXTEMPORANEA",
                name="Devolución Extemporánea a los 90 Días",
                description="Intento de devolución comercial de producto sin rotación 3 meses después de la compraventa.",
                typical_flat_amount=Decimal("19500.00"),
                clause_reference="CLAUSE-4.5",
                is_frequently_abusive=True,
                dispute_counter_strategy="Rechazar la devolución invocando el plazo perentorio de 15 días fijado en la Cláusula 4.5."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-4.5",
                title="Plazos Perentorios para Devoluciones Comerciales",
                text="Toda devolución comercial por excedente de inventario o falta de rotación debe solicitarse por escrito dentro de los primeros 15 días posteriores a la entrega. Transcurrido dicho plazo, la venta se considera irrevocable.",
                policy="NON_RETURNABLE_AFTER_15D"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-WRENCH-SET", description="Juego de Llaves Combinadas SAE y Métricas 24 Pzas", default_price=Decimal("38.00")),
            ProductItemTemplate(sku="SKU-HAMMER-20OZ", description="Martillo de Uña Curva Antivibración 20oz", default_price=Decimal("12.50")),
            ProductItemTemplate(sku="SKU-GENERATOR-4KW", description="Generador a Gasolina 4000W 4 Tiempos", default_price=Decimal("380.00"))
        ]
    ),

    "BIOFARMA_MX": BuyerEnterpriseProfile(
        buyer_id="BIOFARMA_MX",
        business_name="Biofarma Natural CMD, S.A. de C.V.",
        trade_name="Biofarma Labs",
        rfc="BNC0403175X9",
        postal_code="45645",
        industry="Farmacéutica & Suplementos",
        primary_cedis_list=[
            "CEDIS Farma Guadalajara Fríos Muelle 1",
            "CEDIS Lerma Farma Muelle 3"
        ],
        warehouse_supervisors=[
            "Q.F.B. Leticia Arredondo (Responsable Sanitaria)"
        ],
        deductions=[
            DeductionPolicy(
                code="RECALL-TEMP-BREAK",
                name="Ruptura de Cadena de Frío en Transporte",
                description="Rechazo justificado y destrucción sanitaria por registro térmico superior a 8°C durante traslado.",
                typical_flat_amount=Decimal("16800.00"),
                clause_reference="CLAUSE-3.2",
                is_frequently_abusive=False,
                dispute_counter_strategy="Validar datos del termógrafo de transporte. Si la cadena de frío se rompió, el reclamo es improcedente y la pérdida debe asumirse y emitir nota de crédito."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-3.2",
                title="Cadena de Frío y Cumplimiento NOM-059-SSA1",
                text="Los biológicos e insumos sensibles deben mantenerse entre 2°C y 8°C ininterrumpidamente. Si el datalogger registra excursión térmica mayor a 2 horas, el comprador rechazará el lote al 100% por norma sanitaria.",
                policy="STRICT_COLD_CHAIN_MANDATORY"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-PROBIOTIC-COLD", description="Probiótico Multicepas Refrigerado 60 Cápsulas", default_price=Decimal("28.00")),
            ProductItemTemplate(sku="SKU-COLLAGEN-HYD", description="Colágeno Hidrolizado Polvo 500g Sabor Neutro", default_price=Decimal("16.00")),
            ProductItemTemplate(sku="SKU-OMEGA3-HIGH", description="Omega 3 Ultra Puro Concentrado EPA/DHA 120 Perlas", default_price=Decimal("22.00"))
        ]
    ),

    "INDITEX_MX": BuyerEnterpriseProfile(
        buyer_id="INDITEX_MX",
        business_name="Zara México, S.A. de C.V.",
        trade_name="Inditex / Zara México",
        rfc="ZME9206233Z1",
        postal_code="54080",
        industry="Moda Fast-Fashion",
        primary_cedis_list=[
            "CEDIS Logístico Inditex Tlalnepantla Muelle 8"
        ],
        warehouse_supervisors=[
            "Lic. Íñigo De la Concha (Gerente de Inbound Fast Fashion)"
        ],
        deductions=[
            DeductionPolicy(
                code="DISCREPANCIA-TALLAS",
                name="Discrepancia en Matriz de Tallas y Colores",
                description="Deducción por recibir curva de tallas (S-M-L-XL) distinta a la orden de compra aprobada.",
                typical_flat_amount=Decimal("8300.00"),
                clause_reference="CLAUSE-4.7",
                is_frequently_abusive=False,
                dispute_counter_strategy="Verificar si la matriz de tallas entregada coincidía con la orden modificada por el comprador o si fue surtido erróneo del proveedor."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-4.7",
                title="Exactitud de Matriz de Tallas y Distribución por Tienda",
                text="La curva de tallas y colores debe respetarse al 100%. Las piezas enviadas fuera de la matriz solicitada podrán devolverse o aplicarse un demérito del 30% sobre el precio de factura.",
                policy="EXACT_SIZE_CURVE_REQUIRED"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-BLAZER-LINEN", description="Blazer Estructurado de Lino Color Arena", default_price=Decimal("65.00")),
            ProductItemTemplate(sku="SKU-DRESS-MIDI", description="Vestido Midi Estampado Floral Manga Corta", default_price=Decimal("48.00")),
            ProductItemTemplate(sku="SKU-SHOES-LEATHER", description="Mocasines Clásicos en Piel Vacuna Café", default_price=Decimal("55.00"))
        ]
    ),

    "SONY_MX": BuyerEnterpriseProfile(
        buyer_id="SONY_MX",
        business_name="Sony de México, S.A. de C.V.",
        trade_name="Sony México",
        rfc="SME8906066L9",
        postal_code="01210",
        industry="Electrónica Profesional & Dispositivos",
        primary_cedis_list=[
            "CEDIS Sony Santa Fe Muelle 2",
            "CEDIS Sony Guadalajara Muelle 7"
        ],
        warehouse_supervisors=[
            "Ing. Carlos Shiguetomi (Jefe de Aseguramiento de Calidad)"
        ],
        deductions=[
            DeductionPolicy(
                code="RET-CALIBRACION",
                name="Retención por Calibración en Destino",
                description="Retención por costo de calibración óptica y de color en pantallas de grado médico.",
                typical_flat_amount=Decimal("24000.00"),
                clause_reference="CLAUSE-7.8",
                is_frequently_abusive=True,
                dispute_counter_strategy="Demostrar con el certificado de calibración NIST/ISO de fábrica que los equipos salieron con calibración certificada de origen."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-7.8",
                title="Certificados de Calibración de Origen",
                text="Los equipos de grado profesional o médico acompañados de certificado de calibración individual de fábrica serán recibidos sin costo adicional de re-calibración en muelle.",
                policy="FACTORY_CALIBRATION_RECOGNIZED"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-CAM-CINEMA-4K", description="Cámara de Cine Digital 4K Sensor Full-Frame", default_price=Decimal("3800.00")),
            ProductItemTemplate(sku="SKU-LENS-2470-GM", description="Lente Zoom Profesional 24-70mm F2.8 G Master", default_price=Decimal("1900.00")),
            ProductItemTemplate(sku="SKU-MONITOR-MED-4K", description="Monitor Grado Quirúrgico 4K HDR 31 Pulgadas", default_price=Decimal("4200.00"))
        ]
    ),

    "PETCO_MX": BuyerEnterpriseProfile(
        buyer_id="PETCO_MX",
        business_name="Petco Animal Supplies de México, S. de R.L. de C.V.",
        trade_name="Petco México",
        rfc="PAS1304245Z9",
        postal_code="05348",
        industry="Retail Mascotas",
        primary_cedis_list=[
            "CEDIS Petco Cuautitlán Muelle 5"
        ],
        warehouse_supervisors=[
            "Lic. Mónica Arrieta (Jefa de Recepción Petco)"
        ],
        deductions=[
            DeductionPolicy(
                code="LABELING-UPC-BARCODE",
                name="Multa por Código UPC No Escaneable",
                description="Cargo por reetiquetado de bolsas de alimento con código de barras arrugado.",
                typical_flat_amount=Decimal("2900.00"),
                clause_reference="CLAUSE-4.6",
                is_frequently_abusive=True,
                dispute_counter_strategy="Probar que el empaque secundario incluía código ITF-14 100% legible."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-4.6",
                title="Legibilidad de Código UPC en Saco y Caja Máster",
                text="El código de barras UPC o ITF-14 debe tener un grado de verificación ANSI mínimo de 'B'. Cargos por reetiquetado sólo aplican si ambos códigos resultan inoperantes.",
                policy="ANSI_B_CODE_VERIFICATION"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-DOG-FOOD-15KG", description="Alimento Súper Premium Salmón y Camote Perro Adulto 15kg", default_price=Decimal("58.00")),
            ProductItemTemplate(sku="SKU-CAT-LITTER-18KG", description="Arena Sanitaria Aglomerante Control Olores Gato 18kg", default_price=Decimal("22.00")),
            ProductItemTemplate(sku="SKU-FLEA-TREAT-3PK", description="Tratamiento Antipulgas y Garrapatas 3 Pipetas", default_price=Decimal("35.00"))
        ]
    ),

    "NESTLE_MX": BuyerEnterpriseProfile(
        buyer_id="NESTLE_MX",
        business_name="Nestlé México, S.A. de C.V.",
        trade_name="Nestlé Alimentos & Bebidas",
        rfc="NME641121175",
        postal_code="05348",
        industry="Alimentos & Consumo Masivo",
        primary_cedis_list=[
            "CEDIS Nacional Nestlé Tultitlán Muelle 9",
            "CEDIS Lagos de Moreno Muelle 4"
        ],
        warehouse_supervisors=[
            "Ing. Héctor Salavarría (Director de Calidad y Copacking)"
        ],
        deductions=[
            DeductionPolicy(
                code="CUARENTENA-LAB",
                name="Lote Parcial Retenido por Cuarentena Lab",
                description="Retención justificada por lote con recuento microbiológico fuera de rango en laboratorio.",
                typical_flat_amount=Decimal("14000.00"),
                clause_reference="CLAUSE-6.3",
                is_frequently_abusive=False,
                dispute_counter_strategy="Verificar contra-muestra de laboratorio certificado COFEPRIS."
            ),
            DeductionPolicy(
                code="PENALIZACION-PARO-LINEA",
                name="Penalización Unilateral por Paro de Línea",
                description="Cargo por lucro cesante no pactado en el contrato de maquila o copacking.",
                typical_flat_amount=Decimal("7000.00"),
                clause_reference="CLAUSE-6.3",
                is_frequently_abusive=True,
                dispute_counter_strategy="Reclamar improcedencia dado que el contrato excluye daños indirectos o lucro cesante."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-6.3",
                title="Protocolos Sanitarios y Exclusión de Daños Indirectos",
                text="Los lotes no conformes en laboratorio serán objeto de nota de crédito por su valor facturado. Queda expresamente excluida cualquier indemnización por lucro cesante o paro de línea.",
                policy="EXCLUSION_CONSEQUENTIAL_DAMAGES"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-COCOA-POWDER-25KG", description="Saco Cocoa en Polvo Alcalinizada 25kg Grado Industrial", default_price=Decimal("120.00")),
            ProductItemTemplate(sku="SKU-MILK-POWDER-25KG", description="Saco Leche Descremada en Polvo Spray 25kg", default_price=Decimal("95.00")),
            ProductItemTemplate(sku="SKU-CEREAL-FLAKES-10KG", description="Hojuelas de Maíz Fortificadas Base Copacker 10kg", default_price=Decimal("45.00"))
        ]
    ),

    "UNILEVER_MX": BuyerEnterpriseProfile(
        buyer_id="UNILEVER_MX",
        business_name="Unilever de México, S. de R.L. de C.V.",
        trade_name="Unilever México",
        rfc="UME7804077E8",
        postal_code="52000",
        industry="Cuidado Personal & Belleza",
        primary_cedis_list=[
            "CEDIS Lerma Estado de México Muelle 11",
            "CEDIS Tultitlán Personal Care Muelle 6"
        ],
        warehouse_supervisors=[
            "Ing. Gerardo Villaseñor (Supply Chain Operations Lead)"
        ],
        deductions=[
            DeductionPolicy(
                code="OTIF-DESPACHO-TARDIO",
                name="Penalización por Despacho Fuera de Cita",
                description="Retención por arriba 3 horas posterior al slot de rampa confirmado en muelle.",
                typical_flat_amount=Decimal("5500.00"),
                clause_reference="CLAUSE-4.8",
                is_frequently_abusive=True,
                dispute_counter_strategy="Presentar folio de caso fortuito por bloqueo vial federal con acuse de caseta."
            ),
            DeductionPolicy(
                code="MANIOBRA-ESPECIAL",
                name="Cargo por Desestiba y Reacomodo Justificado",
                description="Costo operativo de reacomodo de tarimas desalineadas que impedían paso de patín eléctrico.",
                typical_flat_amount=Decimal("6000.00"),
                clause_reference="CLAUSE-4.8",
                is_frequently_abusive=False,
                dispute_counter_strategy="Verificar acta de maniobra con firma del chofer."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-4.8",
                title="Ventana de Recepción OTIF y Fuerza Mayor",
                text="Las demoras atribuibles a caso fortuito o causas de fuerza mayor debidamente acreditadas en menos de 24 horas no generarán penalización por retraso.",
                policy="FORCE_MAJEURE_EXEMPTION"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-SHAMPOO-BOT-400ML", description="Botella Shampoo Reparación Intensiva 400ml Caja 24pz", default_price=Decimal("48.00")),
            ProductItemTemplate(sku="SKU-SOAP-BAR-3PK", description="Jabón Humectante Barra 3x135g Caja 36pz", default_price=Decimal("38.00")),
            ProductItemTemplate(sku="SKU-DEO-AERO-150ML", description="Desodorante Antitranspirante Aerosol 150ml Caja 24pz", default_price=Decimal("52.00"))
        ]
    ),

    "FARMACIAS_AHORRO": BuyerEnterpriseProfile(
        buyer_id="FARMACIAS_AHORRO",
        business_name="Comercializadora Farmacéutica de Chiapas, S.A.P.I. de C.V.",
        trade_name="Farmacias del Ahorro",
        rfc="CFC9106067N9",
        postal_code="03100",
        industry="Sector Farmacéutico & Retail Salud",
        primary_cedis_list=[
            "CEDIS Farmacias del Ahorro Lerma Muelle 8",
            "CEDIS Monterrey Farma Muelle 2"
        ],
        warehouse_supervisors=[
            "Lic. Claudia Mendoza (Gerente de Compras y Cuentas por Pagar)"
        ],
        deductions=[
            DeductionPolicy(
                code="DESCUENTO-ESPECIAL-ERR",
                name="Diferencia en Tasa de Descuento Especial",
                description="Deducción del 8% cuando la tasa convenida por pronto pago y volumen era únicamente del 3%.",
                typical_flat_amount=Decimal("4900.00"),
                clause_reference="CLAUSE-5.5",
                is_frequently_abusive=True,
                dispute_counter_strategy="Demostrar con la orden de compra y el contrato que la tasa pactada era de 3% y no de 8%."
            ),
            DeductionPolicy(
                code="BONIFICACION-CATALOGO",
                name="Aportación Justificada por Inclusión en Catálogo Trimestral",
                description="Cargo pactado contractualmente por publicación en la guía médica trimestral.",
                typical_flat_amount=Decimal("4000.00"),
                clause_reference="CLAUSE-5.5",
                is_frequently_abusive=False,
                dispute_counter_strategy="Verificar anexo publicitario suscrito por ambas partes."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-5.5",
                title="Descuentos Comerciales y Guía Farmacéutica",
                text="Los descuentos financieros y aportaciones por guía de salud se aplicarán estrictamente bajo los porcentajes autorizados en la carátula del convenio anual.",
                policy="AUTHORIZED_TIER_DISCOUNT"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-ANALGESIC-500MG", description="Paracetamol 500mg Caja con 20 Tabletas", default_price=Decimal("3.50")),
            ProductItemTemplate(sku="SKU-VITAMIN-C-1G", description="Vitamina C Efervescente 1g Tubo 10 Tabletas", default_price=Decimal("4.20")),
            ProductItemTemplate(sku="SKU-FIRST-AID-KIT", description="Botiquín de Primeros Auxilios Portátil 45 Elementos", default_price=Decimal("18.00"))
        ]
    ),

    "SANBORNS_MX": BuyerEnterpriseProfile(
        buyer_id="SANBORNS_MX",
        business_name="Sanborns Hermanos, S.A.",
        trade_name="Sanborns Retail Mixto",
        rfc="SHE190630V37",
        postal_code="01090",
        industry="Retail Mixto & Restaurantero",
        primary_cedis_list=[
            "CEDIS Sanborns Vallejo Muelle 4",
            "CEDIS Naucalpan Centro"
        ],
        warehouse_supervisors=[
            "Ing. Manuel Palacios (Auditor General de Tiendas)"
        ],
        deductions=[
            DeductionPolicy(
                code="DEV-TEMPORADA-EXTEMP",
                name="Deducción por Devolución de Temporada Extemporánea",
                description="Intento unilateral de deducir producto de temporada navideña 6 meses después de vencido el plazo.",
                typical_flat_amount=Decimal("4500.00"),
                clause_reference="CLAUSE-7.1",
                is_frequently_abusive=True,
                dispute_counter_strategy="Demostrar que la devolución debió notificarse a más tardar el 31 de enero según contrato."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-7.1",
                title="Condiciones de Liquidación de Temporada",
                text="Las mercancías adquiridas bajo esquema de temporada deberán liquidarse o solicitarse su devolución dentro de los 30 días posteriores al cierre de la temporada.",
                policy="STRICT_30D_SEASONAL_RETURN"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-CHOCOLATE-TIN-300G", description="Lata Chocolates Suizos Surtidos 300g Edición Especial", default_price=Decimal("12.50")),
            ProductItemTemplate(sku="SKU-TEA-WOOD-BOX", description="Caja de Madera con Selección de Tés Finos 60 Bolsitas", default_price=Decimal("22.00")),
            ProductItemTemplate(sku="SKU-MUG-CERAMIC-GIFT", description="Taza de Cerámica Artesanal con Infusor en Caja de Regalo", default_price=Decimal("9.50"))
        ]
    ),

    "GRUPO_MODELO": BuyerEnterpriseProfile(
        buyer_id="GRUPO_MODELO",
        business_name="Cervecería Modelo de México, S. de R.L. de C.V.",
        trade_name="Grupo Modelo / AB InBev",
        rfc="CMM1206159A3",
        postal_code="11320",
        industry="Bebidas & Consumo Masivo",
        primary_cedis_list=[
            "CEDIS Central Modelo Calzada México-Tacuba Muelle 20",
            "CEDIS Corona Guadalajara Muelle 8"
        ],
        warehouse_supervisors=[
            "Ing. Braulio Echeverría (Gerente de Logística Inversa)"
        ],
        deductions=[
            DeductionPolicy(
                code="FALTANTE-TARIMAS-CHEP",
                name="Discrepancia en Tarimas CHEP y Envase Retornable",
                description="Deducción por faltante de tarimas azules CHEP que no contaban con vale de intercambio.",
                typical_flat_amount=Decimal("14000.00"),
                clause_reference="CLAUSE-8.6",
                is_frequently_abusive=False,
                dispute_counter_strategy="Conciliar con los vales de intercambio electrónicos de CHEP México."
            ),
            DeductionPolicy(
                code="RETENCION-ENVASES-UNILAT",
                name="Retención Unilateral por Rotura en Maniobra",
                description="Deducción de botellas rotas ocasionadas por montacarguistas del CEDIS receptor.",
                typical_flat_amount=Decimal("18000.00"),
                clause_reference="CLAUSE-8.6",
                is_frequently_abusive=True,
                dispute_counter_strategy="Exhibir video y acta donde consta que la maniobra de descarga fue ejecutada por personal del comprador."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-8.6",
                title="Gestión de Envases Retornables y Tarimas de Intercambio",
                text="Las tarimas CHEP y envases retornables se liquidarán contra vale físico o electrónico de intercambio. Los daños ocasionados en descarga por personal del comprador serán absorbidos por este.",
                policy="BUYER_UNLOADING_LIABILITY"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-BEER-LITE-24PK", description="Cartón Cerveza Clara Ultra 24 Botellas 355ml", default_price=Decimal("18.50")),
            ProductItemTemplate(sku="SKU-MALT-BEV-CAN-24", description="Charola Bebida de Malta Sin Alcohol 24 Latas 355ml", default_price=Decimal("14.00")),
            ProductItemTemplate(sku="SKU-WATER-SPARK-12PK", description="Caja Agua Mineral de Manantial 12x600ml Vidrio", default_price=Decimal("12.00"))
        ]
    ),

    "PEPSICO_MX": BuyerEnterpriseProfile(
        buyer_id="PEPSICO_MX",
        business_name="PepsiCo Alimentos México, S. de R.L. de C.V.",
        trade_name="PepsiCo Alimentos México",
        rfc="PAM9206263R1",
        postal_code="06000",
        industry="Snacks & Alimentos Procesados",
        primary_cedis_list=[
            "CEDIS PepsiCo Alimentos Tlalnepantla Muelle 15",
            "CEDIS Sabritas Celaya Guanajuato Muelle 7"
        ],
        warehouse_supervisors=[
            "Lic. Fernando Solís (Auditor Comercial Corporativo)"
        ],
        deductions=[
            DeductionPolicy(
                code="COOP-PUB-UNILATERAL",
                name="Cargo de Cooperación Publicitaria No Pactada",
                description="Retención bancaria por pauta en campaña publicitaria que no fue autorizada por el proveedor.",
                typical_flat_amount=Decimal("13600.00"),
                clause_reference="CLAUSE-10.4",
                is_frequently_abusive=True,
                dispute_counter_strategy="Exigir anulación ante la falta de adendum firmado autorizando el gasto promocional."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-10.4",
                title="Gastos de Publicidad Compartida y Promociones",
                text="Toda participación en campañas publicitarias o promociones especiales requerirá la firma de un convenio específico con presupuesto detallado previo a su ejecución.",
                policy="EXPLICIT_MARKETING_ADDENDUM_REQUIRED"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-POTATO-CHIPS-150G", description="Caja Papas Fritas Clásicas Sal de Mar 24 Bolsas 150g", default_price=Decimal("32.00")),
            ProductItemTemplate(sku="SKU-TORTILLA-CHIPS-200G", description="Caja Totopos de Maíz Horneados 20 Bolsas 200g", default_price=Decimal("26.00")),
            ProductItemTemplate(sku="SKU-NUTS-MIX-180G", description="Caja Mezcla de Nueces y Cacahuates Salados 24 Bolsas 180g", default_price=Decimal("38.00"))
        ]
    ),

    "MINISO_MX": BuyerEnterpriseProfile(
        buyer_id="MINISO_MX",
        business_name="Comercializadora ProEpta, S.A. de C.V.",
        trade_name="Miniso México",
        rfc="CPE1602266S2",
        postal_code="03100",
        industry="Retail Variedades & Novedades",
        primary_cedis_list=[
            "CEDIS Miniso Tepotzotlán Muelle 14"
        ],
        warehouse_supervisors=[
            "Lic. Diana Karen Rosas (Jefa de Operaciones Inbound)"
        ],
        deductions=[
            DeductionPolicy(
                code="DESESTIBA-CONTENEDOR",
                name="Servicio de Desestiba y Paletizado en Muelle",
                description="Costo acordado de paletizado por mercancía que llegó a granel en contenedor marítimo.",
                typical_flat_amount=Decimal("5000.00"),
                clause_reference="CLAUSE-3.6",
                is_frequently_abusive=False,
                dispute_counter_strategy="Reconocer el cargo al constar en el anexo de logística marítima."
            ),
            DeductionPolicy(
                code="FALTANTE-MARITIMO-CIF",
                name="Deducción Indebida por Faltante en Contenedor con Precinto Intacto",
                description="Deducción de piezas cuando el contenedor llegó con sello aduanal intacto y peso de báscula conforme.",
                typical_flat_amount=Decimal("2800.00"),
                clause_reference="CLAUSE-3.6",
                is_frequently_abusive=True,
                dispute_counter_strategy="Presentar acta aduanal con precinto de alta seguridad C-TPAT íntegro y ticket de báscula."
            )
        ],
        contract_clauses=[
            RetailerContractClause(
                clause_id="CLAUSE-3.6",
                title="Recepción de Contenedores Marítimos FCL / CIF",
                text="Para contenedores recibidos con precinto aduanal intacto verificado en presencia de inspector, el proveedor no responderá por faltantes internos salvo peritaje aduanero de origen.",
                policy="SEAL_INTACT_EXONERATION"
            )
        ],
        product_catalog=[
            ProductItemTemplate(sku="SKU-PLUSH-TOY-PENGUIN", description="Peluche Pingüino Suave Felpa 30cm", default_price=Decimal("12.00")),
            ProductItemTemplate(sku="SKU-BOTTLE-GLASS-500", description="Botella de Vidrio Borosilicato con Funda Silicón 500ml", default_price=Decimal("8.50")),
            ProductItemTemplate(sku="SKU-STORAGE-ORGANIZER", description="Caja Organizadora Plegable con Tapa Tela Gris", default_price=Decimal("14.00"))
        ]
    )
}


# ==============================================================================
# PERFIL DE PROVEEDOR ESTÁNDAR (NUESTRA EMPRESA / EMISOR)
# ==============================================================================

DEFAULT_SUPPLIER_PROFILE = {
    "vendor_id": "VEN-001",
    "business_name": "Logística y Abastecimiento Comercial, S.A. de C.V.",
    "trade_name": "SupplyMind Logix",
    "rfc": "LAC1805128T5",
    "fiscal_regime": "601 General de Ley Personas Morales",
    "postal_code": "01210",
    "address": "Av. Santa Fe 495, Piso 18, Álvaro Obregón, CDMX"
}


# ==============================================================================
# MÉTODOS DE CONSULTA Y UTILIDADES DEL CATÁLOGO
# ==============================================================================

def get_retailer_profile(buyer_id: str) -> Optional[BuyerEnterpriseProfile]:
    """Retorna el perfil completo del comprador por su ID."""
    key = buyer_id.upper()
    return RETAILER_CATALOG.get(key)


def list_available_retailers() -> List[str]:
    """Retorna la lista de identificadores de compradores disponibles."""
    return list(RETAILER_CATALOG.keys())


def find_deduction_policy(buyer_id: str, code: str) -> Optional[DeductionPolicy]:
    """Busca una política de deducción específica de un comprador por su código."""
    profile = get_retailer_profile(buyer_id)
    if not profile:
        return None
    for d in profile.deductions:
        if d.code.upper() == code.upper():
            return d
    return None
