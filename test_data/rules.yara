rule PEfileBasic {
  strings:
    $mz = "MZ"

  condition:
    ($mz at 0)
}

rule PEfile {
  strings:
    $mz = "MZ"
    $pe = "PE"

  condition:
    ($mz at 0) and ($pe at uint32(0x3c))
}
