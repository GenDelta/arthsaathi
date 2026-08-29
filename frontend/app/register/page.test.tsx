import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RegisterPage from "./page";
import { authApi } from "@/lib/api-client";
import { useAuthStore } from "@/store/useAuthStore";
import { useRouter } from "next/navigation";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

// Mock api-client
jest.mock("@/lib/api-client", () => ({
  authApi: {
    register: jest.fn(),
  },
}));

// Mock zustand store
jest.mock("@/store/useAuthStore", () => ({
  useAuthStore: jest.fn(),
}));

describe("RegisterPage", () => {
  const mockPush = jest.fn();
  const mockReplace = jest.fn();
  const mockSetAuth = jest.fn();
  const mockFetchMe = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      replace: mockReplace,
    });
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      setAuth: mockSetAuth,
      fetchMe: mockFetchMe,
    });
  });

  it("renders the registration form correctly in Hindi by default", () => {
    render(<RegisterPage />);
    expect(screen.getByRole("heading", { name: /खाता बनाएं/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /खाता बनाएं/i })).toBeInTheDocument();
  });

  it("handles successful registration", async () => {
    (authApi.register as jest.Mock).mockResolvedValue({
      access_token: "fake-access",
      refresh_token: "fake-refresh",
      user_id: "fake-user-id",
    });

    render(<RegisterPage />);
    
    await userEvent.type(screen.getByLabelText(/पूरा नाम/i), "Test User");
    await userEvent.type(screen.getByLabelText(/मोबाइल नंबर/i), "9876543210");
    await userEvent.type(screen.getByLabelText(/पासवर्ड/i), "password123");
    
    fireEvent.click(screen.getByRole("button", { name: /खाता बनाएं/i }));

    await waitFor(() => {
      expect(authApi.register).toHaveBeenCalledWith({
        name: "Test User",
        phone_number: "+919876543210",
        password: "password123",
        occupation: undefined,
        language_pref: "hi",
      });
      expect(mockSetAuth).toHaveBeenCalled();
      expect(mockFetchMe).toHaveBeenCalled();
      expect(mockReplace).toHaveBeenCalledWith("/");
    });
  });
});
