import "hash"
import "pe"


rule libcrypto_hash
{
  condition:
    hash.md5(0, filesize) == "cc9478ee8d2f0345f383e01bcbc1680d"
}

rule pe_characteristics
{
  condition:
    pe.characteristics & pe.EXECUTABLE_IMAGE
}
