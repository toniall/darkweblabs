# I2P threat-model worksheet — Lab 6.5
# (the Lab 5.7 method, re-run for an I2P target)
#
# Score each column 1 (low) .. 5 (high).  weight = L x I x E.
# Fill this for a SPECIFIC activity - hosting vs visiting, in-network vs
# outproxy - not for "I2P in general". The rows already reflect what shifts
# from the Tor model; the weights are yours.

Role / activity: ____________________________________________________________

threat                          L   I   E   weight   vs Tor (Lab 5.7)
-----------------------------   -   -   -   ------   ------------------------------
application leak / canary       .   .   .   ......   unchanged - app layer ignores net
operator OPSEC mistake          .   .   .   ......   unchanged - persona, reuse, style
exit reads destination/content  .   .   .   ......   ~gone in-network; back via outproxy
NetDB floodfill eclipse (6.2)   .   .   .   ......   NEW - no Tor equivalent
leaseSet gateway harvest (6.3)  .   .   .   ......   NEW - inbound edge is published
correlation (four-tunnel)       .   .   .   ......   harder than Tor's both-ends
being a router yourself         .   .   .   ......   NEW - you carry traffic by default

# Headline: I2P is not MORE anonymous than Tor, it is DIFFERENTLY anonymous.
# The application-leak and OPSEC rows are identical to Lab 5.7 - switching
# networks does nothing for them, which is exactly where to spend hardening.
