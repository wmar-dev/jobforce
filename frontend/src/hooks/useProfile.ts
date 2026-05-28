"use client";

import useSWR from "swr";
import { getProfile, putProfile } from "@/lib/api";
import type { UserProfile } from "@/lib/types";

export function useProfile() {
  const { data, error, isLoading, mutate } = useSWR<UserProfile>(
    "/api/profile",
    getProfile
  );

  const updateProfile = async (updates: UserProfile) => {
    const updated = await putProfile(updates);
    await mutate(updated, false);
    return updated;
  };

  return { data, isLoading, error, updateProfile };
}
