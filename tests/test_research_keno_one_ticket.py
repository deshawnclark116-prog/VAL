import copy,random,unittest
from research_keno_one_ticket import replay,check_against_previous
from val import METHODS

class OneTicketKenoTests(unittest.TestCase):
    def synthetic(self,n=560):
        rng=random.Random(1234)
        return [dict(draw_id=1300+i,date="2026-11-17",
                     numbers=sorted(rng.sample(range(1,81),20)))
                for i in range(n)]

    def test_one_vs_three_exact_count_and_payout(self):
        c=replay(self.synthetic(),warmup=500)
        for m in ("control",)+METHODS:
            x,y=c["models"][m]["one"],c["models"][m]["three"]
            self.assertEqual(x["tickets"],60)
            self.assertEqual(y["tickets"],180)
            self.assertEqual(sum(x["by_matches"].values()),60)
            self.assertEqual(sum(y["by_matches"].values()),180)
            self.assertEqual(x["gross_usd"],2*x["by_matches"]["3"]+
                             20*x["by_matches"]["4"]+450*x["by_matches"]["5"])
            self.assertEqual(x["early"]["n"]+x["late"]["n"],60)

    def test_cross_check_prior_full_distribution(self):
        c=replay(self.synthetic(),warmup=500)
        prev={"results":{"draws":60,"methods":{}}}
        for m,item in c["models"].items():
            q=item["three"]
            prev["results"]["methods"][m]={
                "tickets":q["tickets"],"five":q["five_of_five"],
                "gross":q["gross_usd"],"net":q["net_usd"],
                "distribution":q["by_matches"]}
        self.assertTrue(check_against_previous(c,prev))
        changed=copy.deepcopy(prev)
        changed["results"]["methods"]["ensemble"]["gross"]+=1
        with self.assertRaises(AssertionError):
            check_against_previous(c,changed)

if __name__=="__main__":unittest.main()
