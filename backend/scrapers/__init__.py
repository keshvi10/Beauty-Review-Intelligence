from . import ajio, amazon, myntra, nykaa, tira

PLATFORM_SCRAPERS = {
    amazon.PLATFORM: amazon.fetch,
    nykaa.PLATFORM: nykaa.fetch,
    myntra.PLATFORM: myntra.fetch,
    tira.PLATFORM: tira.fetch,
    ajio.PLATFORM: ajio.fetch,
}
