import "bogus"

rule not_exactly_five_streams
{
    condition:
        bogus.number_of_streams != 5
}
