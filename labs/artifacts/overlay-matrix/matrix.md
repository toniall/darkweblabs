# Overlay comparison matrix — Labs 6.7 + 7.7   (all three networks filled)
#
# Not a scoreboard: no network "wins". It is an input to the weighted threat model
# of Lab 5.7. The right network for a task falls out of the task itself, justified by
# a property below and a row in the weighted model. "Anonymous against whom, for
# what?" is the only version of the question with an answer.

property           Tor                     I2P                      Hyphanet
----------------   ---------------------   ----------------------   ------------------------
what it is         anonymity routing to    anonymity routing to     a distributed datastore;
                   the clearnet & onions   in-network services      you fetch keys, not hosts
trust root         9 signed dir            Kademlia NetDB           content-addressed keys;
                   authorities             (floodfills, daily key)  friend graph in darknet
path / delivery    one bidirectional       four unidirectional      key-routed request through
                   circuit                 tunnels                  the store; store-and-forward
is there a host?   yes (onion service)     yes (eepsite)            no - content outlives its
                                                                    publisher
clearnet exit      yes - exit nodes        no by default; outproxy  no
                                           is a separate choice
naming             onion address = key     addressbook + jump       CHK / SSK / USK; KSK is the
                                           services                 squattable convenience
key exposure       intro points published  inbound gateways in the  none published - there is no
                                           leaseSet                 host or lease to expose
adversary must     run guard + exit and    grind floodfills close   be your friend (darknet) or
                   correlate both ends     to a destination key     run many opennet nodes
persistence        while the host is up    while the host is up     while requested; evicted if
                                                                    not (forgetful store)
latency            low                     low-ish                  high (store-and-forward)
biggest lever      both-ends correlation   floodfill / NetDB        compromised friend (darknet);
                                           eclipse of a target      opennet correlation
reach for it to    browse / serve the      run a block-resistant    publish or store durably and
                   clearnet anonymously    in-network service       deniably; survive takedown

# Let the task choose:
#   clearnet reach or interactive service  -> Tor
#   block-resistant interactive in-network -> I2P (authority-free NetDB)
#   persistent, deniable publishing that
#     survives its publisher being seized  -> Hyphanet (darknet vs a strong adversary)
#
# Unchanged across all three (Labs 5.7 / 6.5 / 7.6): the application-leak and
# operator-OPSEC rows. The transport never fixes what you put in the content or
# how you behave - that is where an operator is actually caught, and where an
# investigator studying one should look first.
