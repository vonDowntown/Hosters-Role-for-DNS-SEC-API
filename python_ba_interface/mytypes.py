import typing
from typing import TypedDict, NotRequired


class CouldNotSetDataExeption(Exception):
    """Raise for specific case when it could not set data"""


class CountNS(TypedDict):
    ns: str
    count: int
    domains: list[str]


class DNS(TypedDict):
    _id: str
    domain: str
    foundRecords: list[str]
    A: NotRequired[list[str]]
    AAAA: NotRequired[list[str]]
    CNAME: NotRequired[list[str]]
    DNAME: NotRequired[list[str]]
    MX: NotRequired[list[str]]
    CAA: NotRequired[list[str]]
    CDNSKEY: NotRequired[list[str]]
    CDS: NotRequired[list[str]]
    CERT: NotRequired[list[str]]
    DLV: NotRequired[list[str]]
    DNSKEY: NotRequired[list[str]]
    DS: NotRequired[list[str]]
    IPSECKEY: NotRequired[list[str]]
    KEY: NotRequired[list[str]]
    KX: NotRequired[list[str]]
    NS: NotRequired[list[str]]
    NSEC: NotRequired[list[str]]
    NSEC3: NotRequired[list[str]]
    NSEC3PARAM: NotRequired[list[str]]
    NSECPARAM: NotRequired[list[str]]
    OPENPGPKEY: NotRequired[list[str]]
    RRSIG: NotRequired[list[str]]
    SHHFP: NotRequired[list[str]]
    TLSA: NotRequired[list[str]]
    TXT: NotRequired[list[str]]
    SFP: NotRequired[list[str]]
    DKIM: NotRequired[list[str]]
    SRV: NotRequired[list[str]]
    NAPTR: NotRequired[list[str]]
    ALIAS: NotRequired[list[str]]
    AFSDB: NotRequired[list[str]]
    SOA: NotRequired[list[str]]
    HINFO: NotRequired[list[str]]
    RP: NotRequired[list[str]]
    LOC: NotRequired[list[str]]
    URL: NotRequired[list[str]]
    URI: NotRequired[list[str]]
    HTTPS: NotRequired[list[str]]
    PTR: NotRequired[list[str]]
    SMIMEA: NotRequired[list[str]]
    SVCB: NotRequired[list[str]]
    SSHFP: NotRequired[list[str]]
    APL: NotRequired[list[str]]
    DHCID: NotRequired[list[str]]
    ISDN: NotRequired[list[str]]
    NINFO: NotRequired[list[str]]
    WKS: NotRequired[list[str]]
    SPF: NotRequired[list[str]]
    DANE: NotRequired[list[str]]
    HIP: NotRequired[list[str]]
    DMARC: NotRequired[list[str]]
    MXE: NotRequired[list[str]]
    ANAME: NotRequired[list[str]]
    POOL: NotRequired[list[str]]
    HTTP: NotRequired[list[str]]
    WR: NotRequired[list[str]]
    HTTPRED: NotRequired[list[str]]
    L32: NotRequired[list[str]]
    L64: NotRequired[list[str]]
    LP: NotRequired[list[str]]
    EUI48: NotRequired[list[str]]
    EUI64: NotRequired[list[str]]
    NID: NotRequired[list[str]]
    CSYNC: NotRequired[list[str]]
    registrar: NotRequired[list[str]]

class PartialDNS(DNS, total=False):
    pass


type RegistrarSearchMethod = typing.Union["Documentation", "Login", "EMail", "RecordScan"]


class RegistrarSearch(TypedDict):
    method: RegistrarSearchMethod
    query: str
    link: str
    notes: str
    time: str


class Registrar(TypedDict):
    id: str
    name: str
    domain: str
    supportedRecordTypes: list[str]
    extraPaidRecordTypes: list[tuple[str, list[str]]]
    ipv4: list[str]
    ipv6: list[str]
    nsServer: list[str]

    source: list[RegistrarSearch]
    notes: str

class PartialRegistrar(Registrar, total=False):
    pass


class AuthDict(TypedDict):
    server: str
    username: str
    password: str


class Percentile:
    def __init__(self, percent_list: list[float], max_value: int, logging: bool = False, description: str = "Status"):
        self.percentiles = percent_list.copy()
        self.percentiles.sort()
        self.max_value = max_value
        self.index = 0
        self.current = 0

        self.logging = logging
        self.description = description

    def add(self, value: int) -> float:
        self.current += value
        while True:
            if self.current / self.max_value <= self.percentiles[self.index]:
                return self.percentiles[self.index]
            else:
                if (self.index) >= len(self.percentiles):
                    print("error: Add to much")
                self.index += 1
                if self.logging:
                    print(f"{self.description}: {self.percentiles[self.index]}")
