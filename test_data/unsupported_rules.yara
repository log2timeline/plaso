import "magic"

rule magic_mimetype
{
  condition:
    magic.mime_type() == "application/x-dosexec"
}
