    dev_avg[c] = avg
    print(f'{c:6} {len(cid_dev[c]):6} {avg*100:7.2f}% {tier:>8} {trend:>8}')

# Auto-classify unknowns by deviation threshold
print('\n=== AUTO-CLASSIFY UNKNOWNS ===')
for c in sorted(dev_avg.keys()):
    if c not in KNOWN_TIERS:
        if dev_avg[c] < 0.03:
            print(f'cid={c}: dev={dev_avg[c]*100:.2f}% → suggest SHARP')
        elif dev_avg[c] < 0.06:
            print(f'cid={c}: dev={dev_avg[c]*100:.2f}% → suggest ASIAN')
        else:
            print(f'cid={c}: dev={dev_avg[c]*100:.2f}% → suggest RETAIL')
