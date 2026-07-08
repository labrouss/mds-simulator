"""Domain ID election / principal switch simulation (simplified FSPF)."""

import random


class DomainManager:
    def __init__(self):
        self.domain_ids = {}   # vsan -> domain_id
        self.principal = {}    # vsan -> switch_wwn

    def assign_domain(self, vsan: int, preferred: int = None) -> int:
        if vsan in self.domain_ids:
            return self.domain_ids[vsan]
        domain = preferred or random.randint(1, 239)
        self.domain_ids[vsan] = domain
        return domain

    def elect_principal(self, vsan: int, local_wwn: str, peer_wwn: str):
        # Lower WWN wins in simplified simulation (real FSPF uses priority + WWN)
        winner = min(local_wwn, peer_wwn)
        self.principal[vsan] = winner
        return winner
