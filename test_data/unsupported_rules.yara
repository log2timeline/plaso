import "dotnet"

rule not_exactly_five_streams
{
    condition:
        dotnet.number_of_streams != 5
}
